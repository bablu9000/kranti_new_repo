# -*- coding: utf-8 -*-
import json
import math
import logging
import requests
from odoo import http, _, exceptions
from odoo.http import request
from .serializers import Serializer
from .exceptions import QueryFormatError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
from contextlib import ExitStack


def error_response(error, msg):
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": 200,
            "message": msg,
            "data": {
                "name": str(error),
                "debug": "",
                "message": msg,
                "arguments": list(error.args),
                "exception_type": type(error).__name__
            }
        }
    }


class OdooAPI(http.Controller):
    current_company_id = 0

    @http.route(
        '/auth/',
        type='http',
        auth='none',
        methods=['POST', 'OPTIONS'],
        csrf=False,
        cors='*'
    )
    def authenticate(self, **kwargs):

        if request.httprequest.method == 'OPTIONS':
            return request.make_response('')

        body = json.loads(
            request.httprequest.data.decode()
        )

        params = body.get('params', {})

        db = params.get('db')
        login = params.get('login')
        password = params.get('password')

        with ExitStack() as stack:

            if not request.db or request.db != db:

                cr = stack.enter_context(
                    odoo.modules.registry.Registry(db).cursor()
                )

                env = odoo.api.Environment(
                    cr,
                    None,
                    {}
                )

            else:

                env = request.env

            credential = {
                'login': login,
                'password': password,
                'type': 'password',
            }

            auth_info = request.session.authenticate(
                env,
                credential
            )

            request.session.db = db

            request._save_session(env)

            session_info = env['ir.http'] \
                .with_user(request.session.uid) \
                .session_info()

            return request.make_json_response({
                'result': session_info
            })

    @http.route(
        '/sale/get_all_sale_details/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def sale_details_api(self):
        # MohAmmaD Changes

        res = request.env['account.move'].search([
            '|',
            ('tally_sync', '=', False),
            ('tally_alter', '=', True),
            ('move_type', '=', 'out_invoice'),
            # ('company_id', '=', self.current_company_id),
            ('state', '!=', 'draft'),
            ('posted_before', '=', True),
            ('invoice_date', '>=', date(2026, 1, 1)),
        ])

        # print('res', res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)

        for data in res:
            result = {}
            result['invoice_no'] = data.name
            result[
                'billing_name'] = data.partner_id.name if data.partner_id.name is not False else data.invoice_partner_display_name
            if data.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'
            result['amount'] = data.amount_total_signed
            result['sale_id'] = data.id
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            result['date'] = data.invoice_date.strftime("%d-%m-%Y"),
            return_data.append(result)

        return return_data

    # MohAmmaD Changes

    @http.route(
        '/sale/get_sale_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_sale_details_api(self, rec_id):

        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'out_invoice'),
             ('state', '!=', 'draft'), ('posted_before', '=', True), ('id', '=', rec_id)])
        sale_item_bucket = []
        sale_service_bucket = []
        item_ids = []
        service_item_ids = []
        sale_data = []
        last_item_id = 0

        is_cgst_sgst = False
        for data in res:
            rounding_amount = 0.0

            if data.invoice_cash_rounding_id:
                rounding_lines = data.line_ids.filtered(
                    lambda line: line.account_id in (
                        data.invoice_cash_rounding_id.profit_account_id,
                        data.invoice_cash_rounding_id.loss_account_id,
                    )
                )

                if rounding_lines:
                    rounding_amount = sum(rounding_lines.mapped('balance'))

            print('rounding_amount:', rounding_amount)

            for account_move_line in data.env['account.move.line'].search(
                    [('tax_line_id', '!=', None), ('move_id', '=', data.id)]):
                if account_move_line.tax_group_id.name == 'CGST' or account_move_line.tax_group_id.name == 'SGST':
                    is_cgst_sgst = True
        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        # print('rounding_amount!!!!!!!!!!!', rounding_amount)
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            if data.state == 'cancel':
                sale_data.append({
                    'invoice_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'invoice_no': data.name,
                    'sale_id': data.id,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # sale->branch_master()->tally_branch_name_mapper,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'address': '',
                    'state': '',
                    'city': '',
                    'country': '',
                    'party_name': '',
                    'buyer_name': '',
                    'roundoff_amount': '',

                })
            else:
                for item in data.invoice_line_ids.sorted('sequence'):
                    result = {}
                    # print('item.product_id.id')
                    # print(item.product_id.id)
                    # print('item.product_id.id')
                    is_item = True
                    if item.product_id.id is not False and item.product_id.product_tmpl_id.type is not False:
                        # print('im in product_id')
                        # print(item.product_id.product_tmpl_id.type)
                        # print('im in product_id')
                        item_ids.append(item.id)
                        # if item.product_id.product_tmpl_id.type == 'consu' or item.product_id.product_tmpl_id.type == 'product':
                        if item.product_id.product_tmpl_id.type == 'consu':
                            # print('im in product_id.product_tmpl_id')

                            if item.account_id.id is not False and item.account_root_id.id is not False:
                                desc = ''
                                print('item.nameitem.nameitem.name')
                                print(item.name)
                                # item_ids.append(item.id)
                                # result['item_name'] = item.name
                                # result['item_name'] = item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result['item_name'] = item.product_id.product_tmpl_id.name
                                print('item.product_id.product_tmpl_id.name')
                                print(item.product_id.product_tmpl_id.name)
                                result['item_description'] = ''
                                result['ppi_deleted'] = 0
                                result['quantity_sales'] = item.quantity
                                result['uom_name'] = item.product_uom_id.name
                                result['price_per_unit_with_tax'] = round(float(item.price_total) / item.quantity, 2)
                                result['price_per_unit_without_tax'] = item.price_unit
                                result['price_without_tax'] = item.price_subtotal
                                result['item_override_tax_rate'] = False
                                total_igst = round(float(item.price_total) - float(item.price_subtotal), 2)
                                result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                                result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['tax_roundoff'] = 0.00
                                result['discount'] = item.discount
                                result['item_total_amount'] = item.price_total
                                result['integrated_tax'] = item.tax_ids.name
                                result['md_tax'] = item.tax_ids.description
                                total_qty += item.quantity
                                print('resultsresults')
                                print(result)

                            sale_item_bucket.append(result)

                        else:
                            is_item = False
                            if item.account_id.id is not False and item.account_root_id.id is not False:
                                desc = ''
                                # service_item_ids.append(item.id)
                                # result['item_name'] = item.name
                                # result['item_name'] = item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result[
                                    'item_name'] = item.product_id.product_tmpl_id.name if item.product_id.product_tmpl_id.name is not False else item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(
                                    item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result['item_description'] = ''
                                result['ppi_deleted'] = 0
                                result['quantity_sales'] = item.quantity
                                result['uom_name'] = item.product_uom_id.name
                                result['price_per_unit_with_tax'] = round(float(item.price_total) / item.quantity, 2)
                                result['price_per_unit_without_tax'] = item.price_unit
                                result['price_without_tax'] = item.price_subtotal
                                result['item_override_tax_rate'] = False
                                total_igst = round(float(item.price_total) - float(item.price_subtotal), 2)
                                result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                                result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['tax_roundoff'] = 0.00
                                result['discount'] = item.discount
                                result['item_total_amount'] = item.price_total
                                result['integrated_tax'] = item.tax_ids.name
                                result['md_tax'] = item.tax_ids.description
                                print('resultsresults1')
                                print(result)

                            sale_service_bucket.append(result)

                    elif item.display_type in ('line_section', 'line_note'):
                        last_item_id = item_ids[-1]
                        newitem = data.invoice_line_ids.search([('id', '=', last_item_id), ('move_id', '=', data.id)])
                        desc += item.name + '\n'
                        # result['item_name'] = newitem.name
                        # result['item_name'] = newitem.product_id.product_tmpl_id.name if newitem.product_id.default_code is False else '[' + str(newitem.product_id.default_code) + '] ' + str(newitem.product_id.product_tmpl_id.name)
                        result[
                            'item_name'] = newitem.product_id.product_tmpl_id.tally_mapper_name if res_config_settings.module_aretx_product_tally and newitem.product_id.product_tmpl_id.tally_mapper_name is not False else newitem.product_id.product_tmpl_id.name if newitem.product_id.default_code is False else '[' + str(
                            newitem.product_id.default_code) + '] ' + str(newitem.product_id.product_tmpl_id.name)
                        result['item_description'] = desc
                        result['ppi_deleted'] = 0
                        result['quantity_sales'] = newitem.quantity
                        result['uom_name'] = newitem.product_uom_id.name
                        result['price_per_unit_with_tax'] = round(float(newitem.price_total) / newitem.quantity, 2)
                        result['price_per_unit_without_tax'] = newitem.price_unit
                        result['price_without_tax'] = newitem.price_subtotal
                        result['item_override_tax_rate'] = False
                        total_igst = round(float(newitem.price_total) - float(newitem.price_subtotal), 2)
                        result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                        result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                        result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                        result['tax_roundoff'] = 0.00
                        result['discount'] = newitem.discount
                        result['item_total_amount'] = newitem.price_total
                        result['integrated_tax'] = newitem.tax_ids.name
                        result['md_tax'] = item.tax_ids.description
                        if is_item is True:
                            sale_item_bucket.pop()
                            sale_item_bucket.append(result)
                        else:
                            sale_service_bucket.pop()
                            sale_service_bucket.append(result)

                address = str(data.partner_id.street if data.partner_id.street is not False else '') + '\n' + str(
                    data.partner_id.street2 if data.partner_id.street2 is not False else '') + '\n' + str(
                    data.partner_id.zip if data.partner_id.zip is not False else '') + '\n'
                sale_data.append({
                    'invoice_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'invoice_no': data.name,
                    'invoice_reference': data.ref,
                    'invoice_user_id': data.invoice_user_id.name,
                    'sale_id': data.id,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'party_name': data.partner_id.name if data.partner_id.name is not False else data.partner_id.name,
                    'buyer_name': data.partner_id.name if data.partner_id.name is not False else data.partner_id.name,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # sale->branch_master()->tally_branch_name_mapper,
                    'contact': data.partner_id.phone,
                    'address': address,
                    'state': data.partner_id.state_id.name,
                    'city': data.partner_id.city,
                    'country': data.partner_id.country_id.name,
                    'party_id': data.partner_id.id,
                    # 'voucher_type': data.journal_id.name,
                    # 'voucher_name': data.journal_id.name,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'vehicle_no': '',
                    # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                    'vehicle_kms': 0,
                    'sale_total_amount': data.amount_total,
                    'sale_amount_without_tax': data.amount_untaxed,
                    'total_quantity': total_qty,
                    'cgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                    'sgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                    'igst': data.amount_tax if is_cgst_sgst == False else 0.00,
                    'reference_no': '',
                    'delivery_note_no': '',
                    'delivery_note_date': '',
                    'despatch_doc_no': '',
                    'despatched_through': '',
                    'destination': '',
                    'bill_landing_no': '',
                    'bill_landing_date': '',
                    'term_of_payment': data.invoice_payment_term_id.name if data.invoice_payment_term_id.name is not False else '',
                    'other_reference': '',
                    'delivery_terms': data.invoice_incoterm_id.name if data.invoice_incoterm_id.name is not False else '',
                    'motor_vehicle_no': '',
                    # data.vehicle_number.x_vehicle_number_id if data.vehicle_number and data.vehicle_number.x_vehicle_number_id is not False else '',
                    # 'narration': data.narration,
                    'narration': data.narration if data.narration is not False else '',
                    'order_number': '',
                    'orderDate': '',
                    'roundoff_amount': rounding_amount,
                    'sale_item': sale_item_bucket,
                    'sale_service': sale_service_bucket,
                    'key': ''
                })
        return sale_data

    @http.route(
        '/purchase/get_all_purchase_details/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def purchase_details_api(self):

        # res = request.env['account.move'].search([('move_type', '=', 'in_invoice'), ('state', '!=', 'draft')])
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'in_invoice'),
             ('state', '!=', 'draft'), ('posted_before', '=', True), ('invoice_date', '>=', date(2026, 1, 1))])
        print('res', res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            result['invoice_no'] = data.name
            result[
                'billing_name'] = data.partner_id.name if data.partner_id.name is not False else data.invoice_partner_display_name
            if data.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'
            # result['amount'] = data.amount_total_signed
            result['amount'] = data.amount_total
            result['purchase_id'] = data.id
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            result['date'] = data.invoice_date.strftime("%d-%m-%Y"),

            return_data.append(result)

        return return_data

    @http.route(
        '/purchase/get_purchase_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_purchase_details_api(self, rec_id):

        res = request.env['account.move'].search([('id', '=', rec_id)])
        # res = request.env['account.move'].search(
        #     ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'in_invoice'),
        #      ('state', '!=', 'draft'), ('posted_before', '=', True), ('id', '=', rec_id)])
        purchase_item_bucket = []
        purchase_service_bucket = []
        item_ids = []
        service_item_ids = []
        purchase_data = []
        last_item_id = 0
        # account_move_lines = self.env['account.move.line'].search(
        # [('tax_line_id', '!=', None), ('move_id', '=', self.id)])
        # data = []
        is_cgst_sgst = False
        for data in res:
            for account_move_line in data.env['account.move.line'].search(
                    [('tax_line_id', '!=', None), ('move_id', '=', data.id)]):
                if account_move_line.tax_group_id.name == 'CGST' or account_move_line.tax_group_id.name == 'SGST':
                    is_cgst_sgst = True
        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            if data.state == 'cancel':
                purchase_data.append({
                    'invoice_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'invoice_no': data.name,
                    'supplier_invoice_no': data.ref,
                    'supplier_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'purchase_id': data.id,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # sale->branch_master()->tally_branch_name_mapper,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'address': '',
                    'state': '',
                    'city': '',
                    'country': '',
                    'party_name': '',
                    'supplier_name': '',
                    'roundoff_amount': '',

                })
            else:
                for item in data.invoice_line_ids.sorted('sequence'):
                    result = {}
                    # print('item.product_id.id')
                    # print(item.product_id.id)
                    # print('item.product_id.id')
                    is_item = True
                    if item.product_id.id is not False and item.product_id.product_tmpl_id.type is not False:
                        # print('im in product_id')
                        # print(item.product_id.product_tmpl_id.type)
                        # print('im in product_id')
                        item_ids.append(item.id)
                        # if item.product_id.product_tmpl_id.type == 'consu' or item.product_id.product_tmpl_id.type == 'product':
                        if item.product_id.product_tmpl_id.type == 'consu':
                            # print('im in product_id.product_tmpl_id')

                            if item.account_id.id is not False and item.account_root_id.id is not False:
                                desc = ''
                                # item_ids.append(item.id)
                                # result['item_name'] = item.name
                                # result['item_name'] = item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result['item_name'] = item.product_id.product_tmpl_id.name
                                result['item_description'] = ''
                                result['ppi_deleted'] = 0
                                result['quantity_purchased'] = item.quantity
                                result['uom_name'] = item.product_uom_id.name
                                result['price_per_unit_with_tax'] = round(float(item.price_total) / item.quantity, 2)
                                result['price_per_unit_without_tax'] = item.price_unit
                                result['price_without_tax'] = item.price_subtotal
                                result['item_override_tax_rate'] = False
                                total_igst = round(float(item.price_total) - float(item.price_subtotal), 2)
                                result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                                result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['tax_roundoff'] = 0.00
                                result['discount'] = item.discount
                                result['item_total_amount'] = item.price_total
                                result['integrated_tax'] = item.tax_ids.name
                                total_qty += item.quantity

                            purchase_item_bucket.append(result)

                        else:
                            is_item = False
                            if item.account_id.id is not False and item.account_root_id.id is not False:
                                desc = ''
                                # service_item_ids.append(item.id)
                                # result['service_name'] = item.name
                                # result['service_name'] = item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result[
                                    'service_name'] = item.product_id.product_tmpl_id.name if item.product_id.product_tmpl_id.name is not False else item.product_id.product_tmpl_id.name if item.product_id.default_code is False else '[' + str(
                                    item.product_id.default_code) + '] ' + str(item.product_id.product_tmpl_id.name)
                                result['item_description'] = ''
                                result['ppi_deleted'] = 0
                                result['quantity_purchased'] = item.quantity
                                result['uom_name'] = item.product_uom_id.name
                                result['price_per_unit_with_tax'] = round(float(item.price_total) / item.quantity, 2)
                                result['price_per_unit_without_tax'] = item.price_unit
                                result['price_without_tax'] = item.price_subtotal
                                result['item_override_tax_rate'] = False
                                total_igst = round(float(item.price_total) - float(item.price_subtotal), 2)
                                result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                                result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                                result['tax_roundoff'] = 0.00
                                result['service_discount'] = item.discount
                                result['service_total_amount'] = item.price_total
                                result['service_tax'] = item.tax_ids.name
                                result['central_tax'] = result['item_cgst']
                                result['state_tax'] = result['item_sgst']

                            purchase_service_bucket.append(result)

                    elif item.display_type in ('line_section', 'line_note'):
                        last_item_id = item_ids[-1]
                        newitem = data.invoice_line_ids.search([('id', '=', last_item_id), ('move_id', '=', data.id)])
                        desc += item.name + '\n'

                        result[
                            'item_name'] = newitem.product_id.product_tmpl_id.name if res_config_settings.module_aretx_product_tally and newitem.product_id.product_tmpl_id.tally_mapper_name is not False else newitem.product_id.product_tmpl_id.name if newitem.product_id.default_code is False else '[' + str(
                            newitem.product_id.default_code) + '] ' + str(newitem.product_id.product_tmpl_id.name)
                        result[
                            'service_name'] = newitem.product_id.product_tmpl_id.tally_mapper_name if res_config_settings.module_aretx_product_tally and newitem.product_id.product_tmpl_id.tally_mapper_name is not False else newitem.product_id.product_tmpl_id.name if newitem.product_id.default_code is False else '[' + str(
                            newitem.product_id.default_code) + '] ' + str(newitem.product_id.product_tmpl_id.name)
                        result['item_description'] = desc
                        result['ppi_deleted'] = 0
                        result['quantity_purchased'] = newitem.quantity
                        result['uom_name'] = newitem.product_uom_id.name
                        result['price_per_unit_with_tax'] = round(float(newitem.price_total) / newitem.quantity, 2)
                        result['price_per_unit_without_tax'] = newitem.price_unit
                        result['price_without_tax'] = newitem.price_subtotal
                        result['item_override_tax_rate'] = False
                        total_igst = round(float(newitem.price_total) - float(newitem.price_subtotal), 2)
                        result['item_igst'] = total_igst if is_cgst_sgst == False else 0.00
                        result['item_cgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                        result['item_sgst'] = float(total_igst / 2) if is_cgst_sgst == True else 0.00
                        result['tax_roundoff'] = 0.00
                        result['discount'] = newitem.discount
                        result['service_discount'] = newitem.discount
                        result['item_total_amount'] = newitem.price_total
                        result['service_total_amount'] = newitem.price_total
                        result['integrated_tax'] = newitem.tax_ids.name
                        result['service_tax'] = newitem.tax_ids.name
                        result['central_tax'] = result['item_cgst']
                        result['state_tax'] = result['item_sgst']
                        if is_item is True:
                            purchase_item_bucket.pop()
                            purchase_item_bucket.append(result)
                        else:
                            purchase_service_bucket.pop()
                            purchase_service_bucket.append(result)

                # address = str(data.partner_id.street)+'\n'+str(data.partner_id.street2)+'\n'+str(data.partner_id.city)+'\n'+str(data.partner_id.state_id.name)+'\n'+str(data.partner_id.country_id.name)+'\n'
                address = str(data.partner_id.street if data.partner_id.street is not False else '') + '\n' + str(
                    data.partner_id.street2 if data.partner_id.street2 is not False else '') + '\n' + str(
                    data.partner_id.zip if data.partner_id.zip is not False else '') + '\n'

                # $purchase_detail[] = array(
                #     'invoice_date' = > $purchase_date_format, 'invoice_no' = > $purchase->purchase_no, 'tally_sync' = > $purchase->tally_sync, 'tally_alter' = > $purchase->tally_alter, 'purchase_id' = > $purchase->purchase_invoice_id, 'party_name' = > $tally_account_name_mapper, 'supplier_name' = > $supplier_name, 'company_name' = > $purchase->company_master()->tally_company_name_mapper, 'branch_name' = > $purchase->branch_master()->tally_branch_name_mapper, 'contact' = > $contact_no, 'address' = > $address, 'state' = > $state, 'city' = > $city, 'country' = > 'India', 'party_id' = > $party_id, 'voucher_type' = > $voucher_type, 'vehicle_no' = > $vehicle_no, 'vehicle_kms' = > $purchase->vehicle_kms, 'purchase_total_amount' = > $purchase->amount_with_roundoff, 'amount_without_tax' = > $purchase->amount_without_tax, 'received_quantity' = > $purchase->received_quantity, 'cgst' = > $purchase->cgst, 'sgst' = > $purchase->sgst, 'igst' = > $purchase->igst, 'reference_no' = > '', 'delivery_note_no' = > '', 'delivery_note_date' = > '', 'despatch_doc_no' = > '', 'despatched_through' = > '', 'destination' = > '', 'bill_landing_no' = > '', 'bill_landing_date' = > '', 'other_reference' = > '', 'narration' = > $purchase->narration, 'order_number' = > '', 'orderDate' = > '', 'purchase_item' = > $purchase_item_bucket, 'purchase_service' = > $purchase_service_bucket, 'roundoff_amount' = > $purchase->roundoff_amount, 'supplier_invoice_no' = > $purchase->supplier_invoice_no, 'supplier_date' = > $supplier_date_format, 'key' = > ''
                #
                # );
                print('data.tally_sync', data.tally_sync)
                purchase_data.append({
                    'invoice_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'invoice_no': data.name,
                    'purchase_id': data.id,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'party_name': data.partner_id.name if data.partner_id.name is not False else data.partner_id.name,
                    'supplier_name': data.partner_id.name if data.partner_id.name is not False else data.partner_id.name,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # purchase->branch_master()->tally_branch_name_mapper,
                    'contact': data.partner_id.phone,
                    'address': address,
                    'state': data.partner_id.state_id.name,
                    'city': data.partner_id.city,
                    'country': data.partner_id.country_id.name,
                    'party_id': data.partner_id.id,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'vehicle_no': '',
                    # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                    'vehicle_kms': 0,
                    'purchase_total_amount': data.amount_total,
                    'amount_without_tax': data.amount_untaxed,
                    'received_quantity': total_qty,
                    'cgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                    'sgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                    'igst': data.amount_tax if is_cgst_sgst == False else 0.00,
                    'reference_no': '',
                    'delivery_note_no': '',
                    'delivery_note_date': '',
                    'despatch_doc_no': '',
                    'despatched_through': '',
                    'destination': '',
                    'bill_landing_no': '',
                    'bill_landing_date': '',
                    'term_of_payment': data.invoice_payment_term_id.name if data.invoice_payment_term_id.name is not False else '',
                    'other_reference': '',
                    'delivery_terms': data.invoice_incoterm_id.name if data.invoice_incoterm_id.name is not False else '',
                    'motor_vehicle_no': '',
                    # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                    'narration': data.narration if data.narration is not False else '',
                    'order_number': '',
                    'orderDate': '',
                    'roundoff_amount': data.round_off_value if hasattr(data, 'round_off_value') else 0,
                    'purchase_item': purchase_item_bucket,
                    'purchase_service': purchase_service_bucket,
                    'supplier_invoice_no': data.ref,
                    'supplier_date': data.invoice_date.strftime("%d-%m-%Y"),
                    'key': ''
                })
        return purchase_data

    # @http.route(
    #     '/payment/get_all_payment_details/',
    #     type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    # def payment_details_api(self):

    # res = request.env['account.move'].search([('move_type', '=', 'entry'), ('state', '!=', 'draft'), ('payment_state', '=', None), ('payment_id.payment_type', '=', 'outbound')])
    # res = request.env['account.move'].search(
    # ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
    #  ('state', '!=', 'draft'), ('posted_before', '=', True), ('payment_state', '=', None),
    #  ('company_id', '=', self.current_company_id), ('payment_id.payment_type', '=', 'outbound')])

    # commented on 27 august
    # res = request.env['account.move'].search(
    #     ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('state', '!=', 'draft'),
    #      ('move_type', '=', 'entry'), ('posted_before', '=', True), ('payment_id.payment_type', '=', 'outbound'),
    #      ('payment_id.is_internal_transfer', '=', False),('date', '>=', date(2026, 1, 1))])
    # commented on 27 august

    # payments = request.env['account.payment'].search([
    #     ('state', '=', 'paid'),
    #     ('payment_type', '=', 'outbound'),
    #     ('date', '>=', date(2026, 1, 1)),
    # ])

    # payment_records = request.env['account.payment'].search([
    #     ('state', '=', 'paid'),
    #     ('payment_type', '=', 'outbound'),
    #     # ('is_internal_transfer', '=', False),
    #     ('date', '>=', date(2026, 1, 1)),
    # ])
    #
    # # Fetch corresponding journal entries with sync status
    # payments = request.env['account.move'].search([
    #     ('id', 'in', payment_records.mapped('move_id').ids),
    #     '|',
    #     ('tally_sync', '=', False),
    #     ('tally_alter', '=', True),
    # ])
    #
    #
    # return_data = []
    #
    # res_config_settings = request.env['res.config.settings'].search(
    #     [], order="id desc", limit=1
    # )
    #
    # for data in payments:
    #     move = data.move_id
    #
    #     result = {}
    #     result['payment_no'] = data.name
    #     result['billing_name'] = data.partner_id.name
    #
    #     if data.state == 'cancel':
    #         result['billing_name'] = '<span style="color:red">PURGED</span>'
    #
    #     result['amount'] = data.amount
    #     result['payment_id'] = data.id
    #
    #     # tally fields are on account.move
    #     result['tally_sync'] = move.tally_sync if move else False
    #     result['tally_alter'] = move.tally_alter if move else False
    #
    #     result['date'] = data.date.strftime("%d-%m-%Y")
    #
    #     return_data.append(result)
    #
    # return return_data
    @http.route(
        '/payment/get_all_payment_details/',
        type='json',
        auth='user',
        methods=["POST"],
        csrf=False,
        cors='*'
    )
    def payment_details_api(self):

        # 1. Fetch payment records
        payment_records = request.env['account.payment'].search([
            ('state', '=', 'paid'),
            ('payment_type', '=', 'outbound'),
            ('date', '>=', date(2026, 1, 1)),
        ])

        # 2. Fetch corresponding account.move records
        moves = request.env['account.move'].search([
            ('id', 'in', payment_records.mapped('move_id').ids),
            '|',
            ('tally_sync', '=', False),
            ('tally_alter', '=', True),
        ])

        return_data = []

        # Optional: create mapping for better lookup
        payment_by_move = {
            payment.move_id.id: payment
            for payment in payment_records
        }

        for move in moves:
            payment = payment_by_move.get(move.id)

            if not payment:
                continue

            result = {}

            # Payment fields
            result['payment_no'] = move.name
            result['billing_name'] = payment.partner_id.name or ''
            result['amount'] = payment.amount
            result['payment_id'] = move.id

            # Tally fields from account.move
            result['tally_sync'] = move.tally_sync
            result['tally_alter'] = move.tally_alter

            result['date'] = payment.date.strftime("%d-%m-%Y")

            if move.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'

            return_data.append(result)

        return return_data

    @http.route(
        '/payment/get_payment_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_payment_details_api(self, rec_id):

        # res = request.env['account.move'].search([('id', '=', rec_id)])
        res1 = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
             ('state', '!=', 'draft'), ('posted_before', '=', True), ('payment_state', '=', None),
             ('id', '=', rec_id)])

        res = request.env['account.move'].search(
            [('id', '=', rec_id)])

        print('res', res)

        payment_item_bucket = []
        payment_service_bucket = []
        item_ids = []
        ledger_mapper_details = []
        payment_ref_details = []
        payment_data = []
        last_item_id = 0
        # account_move_lines = self.env['account.move.line'].search(
        # [('tax_line_id', '!=', None), ('move_id', '=', self.id)])
        # data = []
        is_cgst_sgst = False

        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        transaction_type = {'bank': 'E-FUND TRANSFER', 'cash': 'CASH', 'cheque': 'CHEQUE'}

        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            bank_name = {'bank': data.journal_id.name, 'cash': ''}
            l_data = {}
            ref_data = {}
            i_no = ''
            ref = '1'  # agst_ref
            ref_name = 'Agst Ref'
            # t_type = data.journal_id.type
            # if 'bank_reference' in data.payment_id and data.payment_id.bank_reference is not False:
            #     i_no = data.payment_id.bank_reference
            # elif 'cheque_reference' in data.payment_id and data.payment_id.cheque_reference is not False:
            #     i_no = data.payment_id.cheque_reference
            #     t_type = 'cheque'
            t_type = data.journal_id.type
            i_no = False

            payment = request.env['account.payment'].search([
                ('move_id', '=', data.id)
            ], limit=1)

            if payment:
                t_type = payment.journal_id.type

                if getattr(payment, 'bank_reference', False):
                    i_no = payment.bank_reference

                elif getattr(payment, 'cheque_reference', False):
                    i_no = payment.cheque_reference
                    t_type = 'cheque'
            else:
                t_type = data.journal_id.type

            l_data['transaction_type'] = transaction_type.get(t_type, '')
            l_data['instrument_no'] = i_no
            l_data['instrument_date'] = data.date.strftime("%Y%m%d")
            l_data['instrument_date'] = data.date
            l_data['bank_name'] = bank_name[data.journal_id.type]
            ledger_mapper_details.append(l_data)
            # print()
            # item = data.invoice_line_ids.search([('reconciled', '=', False)])[0]
            # 30-09-2025#item = request.env['account.move.line'].search([('move_id', '=', data.id), ('reconciled', '=', False)])[0]
            # for item in data.invoice_line_ids.search([('reconciled', '=', False)]):
            # print('item')
            # print(item)
            # print('item')
            domain = [('move_id', '=', data.id), ('reconciled', '=', False)]
            lines = request.env['account.move.line'].search(domain, order='id asc', limit=2)

            item = lines[0] if len(lines) > 0 else False
            item1 = lines[1] if len(lines) > 1 else False

            kasar_ledger_account = ''
            kasar_amount = ''
            md = ''
            if item1:
                kasar_ledger_account = item1.account_id.name
                kasar_amount = item1.credit
                md = item.credit
            print(kasar_ledger_account)
            print(kasar_amount)
            print(md)
            # return False
            if item.debit > 0.00:
                # cr_dr = 'DR'
                cr_dr = 'CR'
                amount_received = item.debit
            else:
                # cr_dr = 'CR'
                cr_dr = 'DR'
                amount_received = item.credit
            # credit_move_id = data.invoice_line_ids.search([('reconciled', '=', True)])[0].id
            # credit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id), ('reconciled', '=', True)])[0].id
            # before
            # debit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id)])[-1].id
            # 30-09-2025
            debit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id)])[1].id
            # reconciled_res = request.env['account.partial.reconcile'].search([('credit_move_id', '=', credit_move_id)])[0].debit_move_id

            reconciled_res1 = request.env['account.partial.reconcile'].search([('debit_move_id', '=', debit_move_id)])
            message = 'Unlink Payment';

            print('debit_move_id', debit_move_id)
            print('reconciled_res1', reconciled_res1)
            print('kasar_ledger_account', kasar_ledger_account)
            if (not reconciled_res1) and (not kasar_amount):
                # print('Please Linked The Receipt In The Invoice To Add')
                return message
            for reconciled_res in reconciled_res1:
                ref_data = {}
                res_inv = request.env['account.move.line'].search([('id', '=', reconciled_res.credit_move_id.id)])
                print('res_inv', res_inv)
                res_original_inv = request.env['account.move'].search([('id', '=', res_inv.move_id.id)])
                print('res_original_inv', res_original_inv)
                if not res_original_inv:
                    print('Please Linked The Receipt In The Invoice To Add')
                    return False
                    res_original_inv = request.env['account.move'].search([('id', '=', data.id)])

                tally_ledger_name_mapper = res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name
                # tally_ledger_name_mapper_find = request.env['account.payment'].search([('move_id', '=', res_original_inv.id), ('is_internal_transfer', '!=', False),('destination_journal_id', '!=', False)])
                tally_ledger_name_mapper_find = request.env['account.payment'].search(
                    [('move_id', '=', res_original_inv.id)])
                if tally_ledger_name_mapper_find:
                    tally_ledger_name_mapper = tally_ledger_name_mapper_find.destination_account_id.name
                # print('debit_move_id')
                # print(debit_move_id)
                # print(reconciled_res.debit_move_id.id)
                # print(res_inv.move_id.id)
                # print(res_original_inv)
                # print('credit_move_id')

                # ref_data['reference_no'] = res_original_inv.name
                ref_data['reference_no'] = res_original_inv.ref
                ref_data['ref'] = ref
                ref_data['stack'] = 0
                ref_data['ref_name'] = ref_name
                ref_data['cr_dr'] = cr_dr
                ref_data['amount_received'] = amount_received
                ref_data['bill_total_amount'] = res_inv.credit
                # ref_data['invoice_date'] = res_original_inv.invoice_date.strftime("%d-%m-%Y")

                payment_ref_details.append(ref_data)

            address = str(
                res_original_inv.partner_id.street if res_original_inv.partner_id.street is not False else '') + '\n' + str(
                res_original_inv.partner_id.street2 if res_original_inv.partner_id.street2 is not False else '') + '\n' + str(
                res_original_inv.partner_id.zip if res_original_inv.partner_id.zip is not False else '') + '\n'

            # $payment_detail[] = array(
            #     'payment_id' = > $payment->payment_id, 'tally_sync' = > $payment->tally_sync, 'tally_alter' = > $payment->tally_alter, 'payment_date' = > $payment_date_format, 'payment_date_another_format' = > $payment_date_another_format, 'payment_print_date' = > $payment_print_date_format, 'payment_no' = > $payment->payment_no, 'voucher_id' = > $payment->voucher_id, 'voucher_name' = > $voucher_name, 'tally_ledger_name_mapper' = > $tally_ledger_name_mapper, 'total_amount' = > $payment->total_amount, 'party_name' = > $party_name, 'c_name' = > $c_name, 'gst' = > $gst, 'lable' = > $lable, 'party_id' = > $party_id, 'ledger_mapper_details' = > $ledger_mapper_details, 'payment_ref_details' = > $payment_ref_details, 'bill_payments' = > $bill_payments, 'billing' = > $billing, 'total_pending_amount' = > $total_pending_amount, 'final_amount' = > $final_amount, 'narration' = > $payment->narration, 'company_name' = > $payment->company_master()->tally_company_name_mapper, 'branch_name' = > $payment->branch_master()->tally_branch_name_mapper, 'contact' = > $contact_no, 'address' = > $address, 'state' = > $state, 'city' = > $city, 'country' = > 'India', 'is_new_ref' = > $is_new_ref,
            # );

            payment_data.append({
                'md_amount': md,
                'kasar_ledger_account': kasar_ledger_account,
                'kasar_amount': kasar_amount,
                'payment_date': data.date.strftime("%Y%m%d"),
                'payment_date_another_format': data.date.strftime("%d-%m-%Y"),
                'payment_print_date': data.date.strftime("%d-%M-%Y"),
                'payment_no': data.name,
                'payment_id': data.id,
                'tally_sync': data.tally_sync,
                'tally_alter': data.tally_alter,
                # 'tally_ledger_name_mapper': data.partner_id.name,
                'tally_ledger_name_mapper': tally_ledger_name_mapper,
                # 'tally_ledger_name_mapper': res_original_inv.partner_id.name if res_config_settings.module_aretx_customer_tally and res_original_inv.partner_id.tally_mapper_name is not False else res_original_inv.partner_id.name,
                'total_amount': data.amount_total,
                # 'party_name': data.partner_id.name,
                # 'c_name': data.partner_id.name,
                # 'c_name': res_original_inv.partner_id.name,
                'c_name': res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name,
                'gst': '',
                # 'lable': data.partner_id.name,
                'lable': res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name,
                'ledger_mapper_details': ledger_mapper_details,
                'payment_ref_details': payment_ref_details,
                'company_name': data.company_id.name,
                'branch_name': 'Main Location',  # payment->branch_master()->tally_branch_name_mapper,
                # 'contact': data.partner_id.phone,
                'contact': res_original_inv.partner_id.phone,
                'address': address,
                # 'state': data.partner_id.state_id.name,
                'state': res_original_inv.partner_id.state_id.name,
                # 'city': data.partner_id.city,
                'city': res_original_inv.partner_id.city,
                'country': res_original_inv.partner_id.country_id.name,
                # 'party_id': data.partner_id.id,
                'party_id': res_original_inv.partner_id.id,
                # 'voucher_name': data.journal_id.type,
                # 'voucher_type': data.journal_id.tally_mapper_name,
                'voucher_type': 'Odoo-Payment',
                'voucher_name': 'Odoo-Payment',
                'vehicle_no': '',
                # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                'vehicle_kms': 0,
                'amount_without_tax': data.amount_untaxed,
                'received_quantity': total_qty,
                'cgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                'sgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                'igst': data.amount_tax if is_cgst_sgst == False else 0.00,
                'reference_no': '',
                'delivery_note_no': '',
                'delivery_note_date': '',
                'despatch_doc_no': '',
                'despatched_through': '',
                'destination': '',
                'bill_landing_no': '',
                'bill_landing_date': '',
                'term_of_payment': data.invoice_payment_term_id.name if data.invoice_payment_term_id.name is not False else '',
                'other_reference': '',
                'delivery_terms': data.invoice_incoterm_id.name if data.invoice_incoterm_id.name is not False else '',
                'motor_vehicle_no': '',
                # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                'narration': data.narration if data.narration is not False else '',
                'order_number': '',
                'orderDate': '',
                'roundoff_amount': data.round_off_value if hasattr(data, 'round_off_value') else 0,
                'key': '',

            })
        print(payment_data)
        # return False
        return payment_data
        # return ledger_mapper_details

    @http.route(
        '/receipt/get_all_receipt_details/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def receipt_details_api(self):

        # res = request.env['account.move'].search([('move_type', '=', 'entry'), ('state', '!=', 'draft'), ('payment_state', '=', None), ('payment_id.payment_type', '=', 'inbound')])
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('state', '!=', 'draft'),
             ('move_type', '=', 'entry'), ('posted_before', '=', True), ('payment_ids.payment_type', '=', 'inbound'),
             ('date', '>=', date(2026, 1, 1))])
        # res = request.env['account.move'].search(['|', ('tally_sync', '=', False), ('tally_alter', '=', True),('state', '!=', 'draft'),('payment_id.payment_type', '=', 'inbound')])

        # res1 = request.env['account.move'].search(['|', ('tally_sync', '=', False), ('tally_alter', '=', True),
        #                                            ('payment_id.payment_type', '=', 'inbound')])

        # , ('payment_id.payment_type', '=', 'inbound')
        # MohAmmaD Changes
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            result['receipt_no'] = data.name
            result[
                'billing_name'] = data.partner_id.name if data.partner_id.name is not False else data.invoice_partner_display_name
            if data.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'
            result['amount'] = data.amount_total
            result['receipt_id'] = data.id
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            result['date'] = data.date.strftime("%d-%m-%Y"),
            return_data.append(result)

        return return_data

    @http.route(
        '/receipt/get_receipt_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_receipt_details_api(self, rec_id):
        global res_original_inv
        print('Welcome Superman !')
        print('Welcome Superman !', rec_id)
        # res1 = request.env['account.move'].search(
        #     ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
        #      ('state', '!=', 'draft'), ('posted_before', '=', True), ('payment_state', '=', None),
        #      ('payment_id.payment_type', '=', 'inbound'), ('id', '=', rec_id)])

        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('state', '!=', 'draft'),
             ('id', '=', rec_id)])
        print('res', res)
        receipt_item_bucket = []
        receipt_service_bucket = []
        item_ids = []
        ledger_mapper_details = []
        receipt_ref_details = []
        receipt_data = []
        last_item_id = 0
        # account_move_lines = self.env['account.move.line'].search(
        # [('tax_line_id', '!=', None), ('move_id', '=', self.id)])
        # data = []
        is_cgst_sgst = False

        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        transaction_type = {'bank': 'E-FUND TRANSFER', 'cash': 'CASH', 'cheque': 'CHEQUE'}
        # $ref = '1'; // agst_ref
        # $ref_name = 'Agst Ref'; // agst_ref
        # if ($invoice_ref_check->debit_credit == 'CR')
        #     {
        #     $cr_dr = 'DR';
        #     }
        #     else
        #     {
        #     $cr_dr = 'CR';
        #     }
        #     $receipt_agst_ref_details[] = array(
        #         'rr_id' = > $receipt_ref->receipt_reference_id, 'reference_no' = > $receipt_ref->reference_no, 'ref' = > $ref, 'stack' = > $stack, 'ref_name' = > $ref_name, 'cr_dr' = > $cr_dr, 'amount_received' = > $receipt_ref->amount_received, 'bill_total_amount' = > $pending_amt, // $receipt_ref->bill_total_amount, 'invoice_reference_id' = > $receipt_ref->invoice_reference_id, 'invoice_date' = > date_format(
        #         date_create($invoice_ref_check->invoice_date), "d-m-Y"), 'debit_credit' = > $invoice_ref_check->debit_credit,
        #     );
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            print('data')
            print(data.tally_alter)
            print(data.date.strftime("%Y%m%d"))
            print('data')
            bank_name = {'bank': data.journal_id.name, 'cash': ''}
            l_data = {}
            ref_data = {}
            i_no = ''
            ref = '1'  # agst_ref
            ref_name = 'Agst Ref'
            t_type = data.journal_id.type
            # if 'bank_reference' in data.payment_id and data.payment_id.bank_reference is not False:
            #     i_no = data.payment_id.bank_reference
            # elif 'cheque_reference' in data.payment_id and data.payment_id.cheque_reference is not False:
            #     i_no = data.payment_id.cheque_reference
            #     t_type = 'cheque'
            payment = request.env['account.payment'].search([
                ('move_id', '=', data.id)
            ], limit=1)
            print('payment')
            print(payment)
            print('payment')

            i_no = False

            if payment:
                if getattr(payment, 'bank_reference', False):
                    i_no = payment.bank_reference

                elif getattr(payment, 'cheque_reference', False):
                    i_no = payment.cheque_reference
                    t_type = 'cheque'

            l_data['tally_ledger_name_mapper'] = data.journal_id.name
            l_data['ledger_amount'] = data.amount_total

            l_data['transaction_type'] = transaction_type[t_type]  # bank => E-FUND TRANSFER
            l_data['instrument_no'] = i_no
            l_data['instrument_date'] = data.date.strftime("%Y%m%d")
            # l_data['instrument_date'] = data.date
            l_data['bank_name'] = bank_name[data.journal_id.type]
            ledger_mapper_details.append(l_data)
            print(l_data['instrument_date'])
            # item = data.invoice_line_ids.search([('reconciled', '=', False)])[0]

            domain = [('move_id', '=', data.id), ('reconciled', '=', False)]
            lines = request.env['account.move.line'].search(domain, order='id asc', limit=2)

            item = lines[0] if len(lines) > 0 else False
            item1 = lines[1] if len(lines) > 1 else False

            # item = request.env['account.move.line'].search([('move_id', '=', data.id), ('reconciled', '=', False)])[0]

            # item1 = request.env['account.move.line'].search([('move_id', '=', data.id), ('reconciled', '=', False)])[1]

            # for item in data.invoice_line_ids.search([('reconciled', '=', False)]):
            print('item mdddddddddddddddddd')
            # print(item1.account_id.name)
            # print(item1.debit)
            kasar_ledger_account = ''
            kasar_amount = ''
            md = ''
            if item1:
                kasar_ledger_account = item1.account_id.name
                kasar_amount = item1.debit
                md = item.debit
            print('item mdddddddddddddddddd')
            # return False
            if item.debit > 0.00:
                # cr_dr = 'DR'
                cr_dr = 'CR'
                amount_received = item.debit
            else:
                # cr_dr = 'CR'
                cr_dr = 'DR'
                amount_received = item.credit
            print('amount_received', amount_received)
            # credit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id)])[-1].id
            # credit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id)]).id
            credit_move_id = request.env['account.move.line'].search([('move_id', '=', data.id)])[1].id

            reconciled_res_items = request.env['account.partial.reconcile'].search(
                [('credit_move_id', '=', credit_move_id)])
            message = 'Unlink Receipt';

            print('reconciled_res_items', reconciled_res_items)
            print('kasar_ledger_account', kasar_ledger_account)
            if (not reconciled_res_items) and (not kasar_amount):
                # print('Please Linked The Receipt In The Invoice To Add')
                return message

            # if reconciled_res_items !=
            # {
            #     print('heyyyyyyyy please link to invoice')
            # }

            for reconciled_res in reconciled_res_items:
                ref_data = {}
                res_original_inv = request.env['account.move.line'].browse(reconciled_res.debit_move_id.id)
                print('res_original_inv')
                print(res_original_inv)
                print(res_original_inv.debit)
                print(res_original_inv.credit)

                print('mohammadmmmmmmm')
                print('res_original_inv')
                ref_data['reference_no'] = res_original_inv.move_id.name
                ref_data['ref'] = ref
                ref_data['stack'] = 0
                ref_data['ref_name'] = ref_name
                ref_data['cr_dr'] = cr_dr
                # ref_data['amount_received'] = amount_received
                # ref_data['bill_total_amount'] = res_inv.debit
                ref_data['amount_received'] = reconciled_res.amount
                ref_data['bill_total_amount'] = res_original_inv.debit
                ref_data['invoice_date'] = res_original_inv.move_id.invoice_date.strftime(
                    "%d-%m-%Y") if res_original_inv.move_id.invoice_date is not False else res_original_inv.move_id.date.strftime(
                    "%d-%m-%Y")

                receipt_ref_details.append(ref_data)
            # print('Welcome To Superman')
            # print('res_original_inv.partner_id.street')
            # print(res_original_inv.partner_id)

            address = str(
                res_original_inv.partner_id.street if res_original_inv.partner_id.street is not False else '') + '\n' + str(
                res_original_inv.partner_id.street2 if res_original_inv.partner_id.street2 is not False else '') + '\n' + str(
                res_original_inv.partner_id.zip if res_original_inv.partner_id.zip is not False else '') + '\n'

            # $receipt_detail[] = array(
            #     'receipt_id' = > $receipt->receipt_id, 'tally_sync' = > $receipt->tally_sync, 'tally_alter' = > $receipt->tally_alter, 'receipt_date' = > $receipt_date_format, 'receipt_date_another_format' = > $receipt_date_another_format, 'receipt_print_date' = > $receipt_print_date_format, 'receipt_no' = > $receipt->receipt_no, 'voucher_id' = > $receipt->voucher_id, 'voucher_name' = > $voucher_name, 'tally_ledger_name_mapper' = > $tally_ledger_name_mapper, 'total_amount' = > $receipt->total_amount, 'party_name' = > $party_name, 'c_name' = > $c_name, 'gst' = > $gst, 'lable' = > $lable, 'party_id' = > $party_id, 'ledger_mapper_details' = > $ledger_mapper_details, 'receipt_ref_details' = > $receipt_ref_details, 'bill_payments' = > $bill_payments, 'billing' = > $billing, 'total_pending_amount' = > $total_pending_amount, 'final_amount' = > $final_amount, 'narration' = > $receipt->narration, 'company_name' = > $receipt->company_master()->tally_company_name_mapper, 'branch_name' = > $receipt->branch_master()->tally_branch_name_mapper, 'contact' = > $contact_no, 'address' = > $address, 'state' = > $state, 'city' = > $city, 'country' = > 'India', 'is_new_ref' = > $is_new_ref,
            # );

            receipt_data.append({
                'md_amount': md,
                'kasar_ledger_account': kasar_ledger_account,
                'kasar_amount': kasar_amount,
                'receipt_date': data.date.strftime("%Y%m%d"),
                'receipt_date_another_format': data.date.strftime("%d-%m-%Y"),
                'receipt_print_date': data.date.strftime("%d-%M-%Y"),
                'receipt_no': data.name,
                'receipt_id': data.id,
                'tally_sync': data.tally_sync,
                'tally_alter': data.tally_alter,
                # 'tally_ledger_name_mapper': data.partner_id.name,
                # 'tally_ledger_name_mapper': tally_ledger_name_mapper,
                'tally_ledger_name_mapper': res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name,
                'total_amount': data.amount_total,
                # 'party_name': data.partner_id.name,
                # 'c_name': data.partner_id.name,
                # 'c_name': res_original_inv.partner_id.name,
                'c_name': res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name,
                'gst': '',
                # 'lable': data.partner_id.name,
                'lable': res_original_inv.partner_id.name if res_original_inv.partner_id.name is not False else res_original_inv.partner_id.name,
                'ledger_mapper_details': ledger_mapper_details,
                'receipt_ref_details': receipt_ref_details,
                'company_name': data.company_id.name,
                'branch_name': 'Main Location',  # receipt->branch_master()->tally_branch_name_mapper,
                # 'contact': data.partner_id.phone,
                'contact': res_original_inv.partner_id.phone,
                'address': address,
                # 'state': data.partner_id.state_id.name,
                'state': res_original_inv.partner_id.state_id.name,
                # 'city': data.partner_id.city,
                'city': res_original_inv.partner_id.city,
                'country': res_original_inv.partner_id.country_id.name,
                # 'party_id': data.partner_id.id,
                'party_id': res_original_inv.partner_id.id,
                # 'voucher_name': data.journal_id.type,
                # 'voucher_type': data.journal_id.tally_mapper_name,
                'voucher_type': 'Odoo-Receipt',
                'voucher_name': 'Odoo-Receipt',
                'vehicle_no': '',
                # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                'vehicle_kms': 0,
                'amount_without_tax': data.amount_untaxed,
                'received_quantity': total_qty,
                'cgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                'sgst': float(data.amount_tax / 2) if is_cgst_sgst == True else 0.00,
                'igst': data.amount_tax if is_cgst_sgst == False else 0.00,
                'reference_no': '',
                'delivery_note_no': '',
                'delivery_note_date': '',
                'despatch_doc_no': '',
                'despatched_through': '',
                'destination': '',
                'bill_landing_no': '',
                'bill_landing_date': '',
                'term_of_payment': data.invoice_payment_term_id.name if data.invoice_payment_term_id.name is not False else '',
                'other_reference': '',
                'delivery_terms': data.invoice_incoterm_id.name if data.invoice_incoterm_id.name is not False else '',
                'motor_vehicle_no': '',
                # data.vehicle_number.x_vehicle_number_id if data.vehicle_number.x_vehicle_number_id is not False else '',
                'narration': data.narration if data.narration is not False else '',
                'order_number': '',
                'orderDate': '',
                'roundoff_amount': data.round_off_value if hasattr(data, 'round_off_value') else 0,
                'key': '',

            })
        print(receipt_data)
        # return False
        return receipt_data
        # return ledger_mapper_details

    @http.route(
        '/journal/get_all_journal_details_v2/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def journal_details_api_v2(self):
        # $journal_detail[] = array(
        #     'journal_no' = > $journal_value->journal_no, 'billing_name' = > $billing_name, 'amount' = > $journal_value->amount, 'total_debit_amount' = > $journal_value->total_debit_amount, 'total_credit_amount' = > $journal_value->total_credit_amount, 'journal_id' = > $journal_value->journal_id, 'tally_sync' = > $journal_value->tally_sync,
        # );

        # res = request.env['account.move'].search(
        #     [('move_type', '=', 'entry'), ('state', '!=', 'draft'),
        #      ('journal_id.type', '=', 'general')])
        # , ('journal_id.journal_type', '=', 'outbound')
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
             ('state', '!=', 'draft'), ('posted_before', '=', True),
             ('journal_id.type', 'in', ['general', 'cash', 'bank']),
             ('date', '>=', date(2026, 1, 1))
             # ('payment_ids.is_internal_transfer', '=', True),  # 🔥 new condition
             ])

        # res = request.env['account.payment'].search(
        #     [('is_internal_transfer', '=', False)],
        #     limit=1
        # )

        # print(res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            item = request.env['account.move.line'].search([('move_id', '=', data.id)])[0]
            billing_name = item.account_id.name
            if item.account_id.name == 'Debtors' or item.account_id.name == 'Creditors':
                # check if partner_id exist
                if item.partner_id is not None:
                    billing_name = item.partner_id.tally_mapper_name if item.partner_id.tally_mapper_name is not False else item.partner_id.name
            result['journal_no'] = data.name
            result['billing_name'] = billing_name  # 'Demo' #data.invoice_partner_display_name
            if data.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'
            result['amount'] = data.amount_total
            # result['total_debit_amount'] = data.amount_total
            # result['total_credit_amount'] = data.amount_total
            result['journal_id'] = data.id
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            result['is_internal_transfer'] = 'mohammad'
            # result['tally_alter'] = 0
            return_data.append(result)
        print(return_data)
        return return_data

    @http.route(
        '/journal/get_journal_details_v2/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_journal_details_api_v2(self, rec_id):

        print('welcome Superman !', rec_id)
        # $journal_item_bucket[] = array(
        #     'item_id' = > $journal_item->ledger_id,
        #     'item_name' = > $this->mdl_journal_item->get_ledger_name($journal_item->ledger_id), 'tally_ledger_name_mapper' = > $this->mdl_journal->get_tally_ledger_name($journal_item->ledger_id), 'ledger_description' = > $journal_item->ledger_description,
        #     'ppi_id' = > $journal_item->id,
        #     'item_amount' = > $journal_item->amount,
        #     'item_dr_cr' = > $journal_item->dr_cr,
        # );

        # res = request.env['account.move'].search([('id', '=', rec_id)])
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
             ('state', '!=', 'draft'), ('posted_before', '=', True),
             ('journal_id.type', 'in', ['general', 'cash', 'bank']), ('id', '=', rec_id)])
        journal_item_bucket = []
        journal_service_bucket = []
        item_ids = []
        ledger_mapper_details = []
        journal_item_bucket = []
        journal_data = []
        last_item_id = 0
        # account_move_lines = self.env['account.move.line'].search(
        # [('tax_line_id', '!=', None), ('move_id', '=', self.id)])
        # data = []
        is_cgst_sgst = False

        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        transaction_type = {'bank': 'E-FUND TRANSFER', 'cash': 'CASH', 'cheque': 'CHEQUE'}
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            if data.state == 'cancel':
                journal_data.append({
                    'journal_id': data.id,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'journal_date': data.date.strftime("%Y%m%d"),
                    'due_date': data.date.strftime("%Y%m%d"),
                    'journal_no': data.name,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # sale->branch_master()->tally_branch_name_mapper,
                    'address': '',
                    'state': '',
                    'city': '',
                    'country': '',
                })
            else:
                invoice_line_ids = request.env['account.move.line'].search([('move_id', '=', data.id)])
                # print(data.ref)
                # print(data.invoice_line_ids)
                # print(invoice_line_ids)
                # print('data.invoice_line_ids')
                # for item in data.invoice_line_ids:
                for item in invoice_line_ids:
                    l_data = {}
                    l_data['item_name'] = item.account_id.name
                    l_data['tally_ledger_name_mapper'] = item.account_id.name
                    if item.account_id.name == 'Debtors' or item.account_id.name == 'Creditors':
                        # check if partner_id exist
                        if item.partner_id is not None:
                            l_data[
                                'item_name'] = item.partner_id.name if item.partner_id.name is not False else item.partner_id.name
                            l_data[
                                'tally_ledger_name_mapper'] = item.partner_id.name if item.partner_id.name is not False else item.partner_id.name
                    l_data['item_id'] = item.id
                    l_data['ledger_description'] = item.name if item.name is not False else ''
                    item_amount = item.credit
                    item_dr_cr = 'CR'
                    if item.debit > 0.00:
                        item_amount = item.debit
                        item_dr_cr = 'DR'
                    l_data['item_amount'] = item_amount
                    l_data['item_dr_cr'] = item_dr_cr
                    journal_item_bucket.append(l_data)

                # address = str(res_original_inv.partner_id.street if res_original_inv.partner_id.street is not False else '') + '\n' + str(
                #     res_original_inv.partner_id.street2 if res_original_inv.partner_id.street2 is not False else '') + '\n' + str(
                #     res_original_inv.partner_id.zip if res_original_inv.partner_id.zip is not False else '') + '\n'

                # $journal_detail[] = array(
                #     'journal_id' = > $journal->journal_id,
                #     'is_manual' = > $is_manual,
                #     'voucher_name' = > $voucher_type,
                #     'journal_date' = > $journal_date_format,
                #     'journal_no' = > $journal->journal_no,
                #     'voucher_id' = > $journal->voucher_id,
                #     'item_amount' = > $journal->amount,
                #     'total_debit_amount' = > $journal->total_debit_amount,
                #     'total_credit_amount' = > $journal->total_credit_amount,
                #     'first_item_name' = > $this->mdl_journal->get_ledger_name($journal->ledger_id), 'tally_ledger_name_mapper' = > $this->mdl_journal->get_tally_ledger_name($journal->ledger_id), 'first_item_id' = > $journal->ledger_id,
                #     'journal_item' = > $journal_item_bucket,
                #     'narration' = > $journal->narration,
                #     'reference_no' = > $journal->reference_no,
                #     'due_date' = > $due_date_format,
                #     'company_name' = > $this->mdl_journal->get_tally_company_name_mapper($journal->company_id), 'state' = > $state,
                # );
                tally_ledger_name_mapper_final = data.invoice_line_ids[0].account_id.name
                if data.invoice_line_ids[0].account_id.name == 'Debtors' or data.invoice_line_ids[
                    0].account_id.name == 'Creditors':
                    # check if partner_id exist
                    if data.invoice_line_ids[0].partner_id is not None:
                        tally_ledger_name_mapper_final = data.invoice_line_ids[0].partner_id.tally_mapper_name if \
                            data.invoice_line_ids[0].partner_id.tally_mapper_name is not False else \
                            data.invoice_line_ids[
                                0].partner_id.name
                journal_data.append({
                    'journal_id': data.id,
                    'voucher_type': 'Odoo-Contra',
                    'voucher_name': 'Odoo-Contra',
                    'journal_date': data.date.strftime("%Y%m%d"),
                    'journal_no': data.name,
                    'item_amount': data.amount_total,
                    'tally_ledger_name_mapper': tally_ledger_name_mapper_final,
                    'journal_item': journal_item_bucket,
                    'narration': data.narration if data.narration is not False else '',
                    'reference_no': data.ref if data.ref is not False else '',
                    'due_date': data.date.strftime("%Y%m%d"),
                    'company_name': data.company_id.name,
                    'state': data.company_id.partner_id.state_id.name,
                    # 'tally_sync': 0,
                    # 'tally_alter': 0,

                })
        print(journal_data)
        # return False
        return journal_data
        # return ledger_mapper_details

    @http.route(
        '/product/get_all_product_details2/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def product_details_api(self):
        current_company_id = request.env.company.id
        print("Current Company ID:", current_company_id)

        # Correct domain for product.template
        res = request.env['product.template'].search([
            '|',
            ('tally_sync', '=', False),
            ('tally_alter', '=', True),
            ('active', '=', True)
        ])
        # print("Current res:", res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)

        for data in res:
            result = {}
            # print('data', data)
            # data is product.template now, not product.product
            if data.tally_mapper_name:
                # print('data', data)
                tally_product_name_mapper = data.tally_mapper_name
            else:
                # print('data', data)
                tally_product_name_mapper = data.name
                if data.default_code:
                    tally_product_name_mapper = f"[{data.default_code}] {tally_product_name_mapper}"
            # print('data', data)
            result['product_id'] = data.id
            result['tally_product_name_mapper'] = tally_product_name_mapper
            result['product_ndp'] = data.list_price
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter

            return_data.append(result)
            print("Company result:", result)

        return return_data

    @http.route(
        '/product/get_all_product_details/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def product_details_api(self):

        # res = request.env['product.product'].search(['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('company_id', '=', self.current_company_id), ('active', '=', True)])
        res = request.env['product.template'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('active', '=', True)])
        print('res', res)
        # , ('product_id.product_type', '=', 'outbound')
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)

        for data in res:
            result = {}
            # item = request.env['account.move.line'].search([('move_id', '=', data.id)])[0]

            if data.name is not False:
                tally_product_name_mapper = data.name
            else:
                tally_product_name_mapper = data.name
                # created_date_next_month = date(int(data.create_date.strftime("%Y")), int(data.create_date.strftime("%m")), int(data.create_date.strftime("%d"))) + relativedelta(months=1)

                if data.default_code is not False:
                    tally_product_name_mapper = '[' + str(data.default_code) + '] ' + str(tally_product_name_mapper)
            result['product_id'] = data.id
            result['tally_product_name_mapper'] = tally_product_name_mapper  # 'Demo' #data.invoice_partner_display_name
            result['product_ndp'] = data.list_price
            # Product Tax
            result['product_tax'] = (
                data.taxes_id[0].tax_rate if data.taxes_id else ''
            )

            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            return_data.append(result)

        return return_data

    @http.route(
        '/product/get_product_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_product_details_api(self, rec_id, csrf=False):

        # print('here.......................')
        # print('recid.......................', rec_id)
        current_company = request.env.company

        res = request.env['product.template'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('active', '=', True), ('id', '=', rec_id)])
        # , ('product_id.product_type', '=', 'outbound')
        print('here.......................')
        print('res.......................', res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            # item = request.env['account.move.line'].search([('move_id', '=', data.id)])[0]
            # tally_product_name_mapper = data.product_tmpl_id.name
            created_date_next_month = date(int(data.create_date.strftime("%Y")), int(data.create_date.strftime("%m")),
                                           int(data.create_date.strftime("%d"))) + relativedelta(months=1)

            # if data.default_code is not False:
            #     tally_product_name_mapper = '['+str(data.default_code)+'] '+str(tally_product_name_mapper)

            if data.name:
                tally_product_name_mapper = data.name
            else:
                tally_product_name_mapper = data.name
                if data.default_code:
                    tally_product_name_mapper = '[' + str(data.default_code) + '] ' + str(tally_product_name_mapper)
            print('tally_product_name_mapper', tally_product_name_mapper)
            result['product_id'] = data.id
            result['tally_product_name_mapper'] = tally_product_name_mapper  # 'Demo' #data.invoice_partner_display_name
            result['product_ndp'] = data.list_price
            result['product_uom_id'] = data.uom_id.id
            result['uom_name'] = data.uom_id.name
            result['product_category_id'] = data.categ_id.id
            result['product_category_name'] = data.categ_id.name
            result['product_category_id'] = data.categ_id.id
            result['product_category_name'] = data.categ_id.name
            result['parent_category_id'] = data.categ_id.parent_id.id
            result['parent_category_name'] = data.categ_id.parent_id.name
            result['default_product_category_name'] = data.categ_id.name
            result['default_uom_name'] = data.uom_id.name
            result['created_date_next_month'] = created_date_next_month
            result['company_name'] = current_company.name  # data.create_uid.company_id.name
            result[
                'state'] = current_company.partner_id.state_id.name  # data.create_uid.company_id.partner_id.state_id.name

            return_data.append(result)

        return return_data

    @http.route(
        '/customer/get_all_customer_details/<string:invoice_type>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def customer_details_api(self, invoice_type):
        self.current_company_id = request.env.company.id

        if invoice_type == 'Sale':
            request._cr.execute((
                    '''select res_partner.* from res_partner INNER JOIN account_move ON res_partner.id = account_move.partner_id WHERE account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.move_type IN ('out_invoice','out_receipt','entry') AND COALESCE(res_partner.tally_sync,'false') <> 'true'  OR account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.move_type IN ('out_invoice','out_receipt','entry') AND COALESCE(res_partner.tally_alter,'true') <> 'false'  GROUP BY res_partner.id'''))
        else:
            request._cr.execute((
                    '''select res_partner.* from res_partner INNER JOIN account_move ON res_partner.id = account_move.partner_id WHERE account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.move_type IN ('in_invoice','in_receipt','entry') AND COALESCE(res_partner.tally_sync,'false') <> 'true'  OR account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.company_id =  ''' + str(
                self.current_company_id) + ''' AND account_move.move_type IN ('in_invoice','in_receipt','entry') AND COALESCE(res_partner.tally_alter,'true') <> 'false'  GROUP BY res_partner.id'''))

        res = request._cr.dictfetchall()

        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            result['customer_id'] = data['id']
            result['ledger_name'] = data['name']
            # result['ledger_name'] = data['tally_mapper_name'] if res_config_settings.module_aretx_customer_tally and \                                                                 data['tally_mapper_name'] is not False else data[                'name']
            result['tally_sync'] = data['tally_sync']
            result['tally_alter'] = data['tally_alter']
            result['mobile_number'] = data['mobile'] = data['phone']
            result['date'] = data['tally_sync_date'] if data['tally_sync_date'] else ''
            return_data.append(result)

        return return_data

    @http.route(
        '/customer/get_customer_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_customer_details_api(self, rec_id):
        # $customer_data[] = array(
        #     'billing_shipping_id' = > $billing_shipping->billing_shipping_id,
        #     'company_name' = > $company->tally_company_name_mapper,
        #     'ledger_name' = > $tally_account_name_mapper,
        #     'ledger_name_alias' = > '',
        #     'address' = > $address,
        #     'city' = > $city,
        #     'state' = > $state,
        #     'country' = > 'India',
        #     'email' = > $email,
        #     'cc_email' = > '',
        #     'website' = > $website,
        #     "panCard_number" = > "",
        #     "registration_type" = > $registration_type,
        #     "credit_period" = > "",
        #     "phone_number" = > '',
        #     "fax_number" = > "",
        #     "contact_person_name" = > $contact_person,
        #     "mobile_number" = > $contact_no,
        #     "gst_number" = > $gst,
        #     "credit_limit" = > "",
        #     "pincode" = > $pincode,
        #
        # );
        # res = request.env['res.partner'].search(['|', ('tally_sync', '=', False), ('tally_alter', '=', True),('parent_id', '=', False), ('id', '=', rec_id)])
        res = request.env['res.partner'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('id', '=', rec_id)])

        print('res_partner', res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            address = str(data.street if data.street is not False else '') + '\n' + str(
                data.street2 if data.street2 is not False else '') + '\n'
            registration_type = '&#4; Unknown'
            # registration_type = ''
            # if data.l10n_in_gst_treatment == 'regular' or data.l10n_in_gst_treatment == 'consumer' or data.l10n_in_gst_treatment == 'composition' or data.l10n_in_gst_treatment == 'unregistered':
            #     registration_type = data.l10n_in_gst_treatment.capitalize()
            result['customer_id'] = data.id
            result['company_name'] = request.env['res.company'].browse(
                self.current_company_id).name  # data.create_uid.company_id.name
            result['ledger_name'] = data.name
            # result[
            #     'ledger_name'] = data.tally_mapper_name if res_config_settings.module_aretx_customer_tally and data.tally_mapper_name is not False else data.name
            result['ledger_name_alias'] = ''
            result['address'] = address
            result['city'] = data.city if data.city is not False else ''
            result['state'] = data.state_id.name if data.state_id.name is not False else ''
            result['country'] = data.country_id.name if data.country_id.name is not False else ''
            result['email'] = data.email if data.email is not False else ''
            result['cc_email'] = ''
            result['website'] = data.website if data.website is not False else ''
            result['panCard_number'] = ''
            result['registration_type'] = registration_type
            result['credit_period'] = ''
            result['phone_number'] = ''
            result['fax_number'] = ''
            # result['contact_person_name'] = data.name
            result[
                'contact_person_name'] = data.name if data.name is not False else data.name
            result['mobile_number'] = data.phone if data.phone is not False else data.phone
            result['gst_number'] = data.vat if data.vat is not False else ''
            result['credit_limit'] = data.credit_limit if data.credit_limit is not False else ''
            result['pincode'] = data.zip if data.zip is not False else ''
            result['date'] = data.tally_sync_date
            return_data.append(result)

        return return_data

    @http.route(
        '/tally/tally_sync_done/<string:name>/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def tally_sync_done_api(self, name, rec_id, **post):
        print('superman')
        print('Hey I am Here Start')
        print(self)
        print(name)
        # print(**post)
        # print(rec_id)
        print('Hey I am Here End')
        print('batman')
        message = post['message']
        data = {}
        model = ''
        if name in ['Sale', 'Purchase', 'Receipt', 'Payment', 'Journal']:
            model = 'account.move'
        elif name == 'Customer':
            model = 'res.partner'
        elif name == 'Product':
            model = 'product.template'

        if model != '':
            print(model)
            data['tally_sync'] = True
            data['tally_alter'] = False
            data['tally_sync_date'] = datetime.today()
            # res = request.env['account.move'].search(
            #     ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('id', '=', rec_id)])
            res = request.env[model].search(
                ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('id', '=', rec_id)])
            res.write(data)
        return message

    @http.route(
        '/object/<string:model>/<string:function>',
        type='json', auth='user', methods=["POST"], csrf=False)
    def call_model_function(self, model, function, **post):
        args = []
        kwargs = {}
        if "args" in post:
            args = post["args"]
        if "kwargs" in post:
            kwargs = post["kwargs"]
        model = request.env[model]
        result = getattr(model, function)(*args, **kwargs)
        return result

    @http.route(
        '/object/<string:model>/<int:rec_id>/<string:function>',
        type='json', auth='user', methods=["POST"], csrf=False)
    def call_obj_function(self, model, rec_id, function, **post):
        args = []
        kwargs = {}
        if "args" in post:
            args = post["args"]
        if "kwargs" in post:
            kwargs = post["kwargs"]
        obj = request.env[model].browse(rec_id).ensure_one()
        result = getattr(obj, function)(*args, **kwargs)
        return result

    @http.route(
        '/api/<string:model>',
        type='http', auth='user', methods=['GET'], csrf=False)
    def get_model_data(self, model, **params):
        try:
            records = request.env[model].search([])
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            res = error_response(e, msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        if "query" in params:
            query = params["query"]
        else:
            query = "{*}"

        if "order" in params:
            orders = json.loads(params["order"])
        else:
            orders = ""

        if "filter" in params:
            filters = json.loads(params["filter"])
            records = request.env[model].search(filters, order=orders)

        prev_page = None
        next_page = None
        total_page_number = 1
        current_page = 1

        if "page_size" in params:
            page_size = int(params["page_size"])
            count = len(records)
            total_page_number = math.ceil(count / page_size)

            if "page" in params:
                current_page = int(params["page"])
            else:
                current_page = 1  # Default page Number
            start = page_size * (current_page - 1)
            stop = current_page * page_size
            records = records[start:stop]
            next_page = current_page + 1 \
                if 0 < current_page + 1 <= total_page_number \
                else None
            prev_page = current_page - 1 \
                if 0 < current_page - 1 <= total_page_number \
                else None

        if "limit" in params:
            limit = int(params["limit"])
            records = records[0:limit]

        try:
            serializer = Serializer(records, query, many=True)
            data = serializer.data
        except (SyntaxError, QueryFormatError) as e:
            res = error_response(e, e.msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        res = {
            "count": len(records),
            "prev": prev_page,
            "current": current_page,
            "next": next_page,
            "total_pages": total_page_number,
            "result": data
        }
        return http.Response(
            json.dumps(res),
            status=200,
            mimetype='application/json'
        )

    @http.route(
        '/api/<string:model>/<int:rec_id>',
        type='http', auth='user', methods=['GET'], csrf=False)
    def get_model_rec(self, model, rec_id, **params):
        try:
            records = request.env[model].search([])
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            res = error_response(e, msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        if "query" in params:
            query = params["query"]
        else:
            query = "{*}"

        # TODO: Handle the error raised by `ensure_one`
        record = records.browse(rec_id).ensure_one()

        try:
            serializer = Serializer(record, query)
            data = serializer.data
        except (SyntaxError, QueryFormatError) as e:
            res = error_response(e, e.msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        return http.Response(
            json.dumps(data),
            status=200,
            mimetype='application/json'
        )

    @http.route(
        '/api/<string:model>/',
        type='json', auth="user", methods=['POST'], csrf=False)
    def post_model_data(self, model, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on POST request body"
            raise exceptions.ValidationError(msg)

        try:
            model_to_post = request.env[model]
        except KeyError:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)

        # TODO: Handle data validation

        if "context" in post:
            context = post["context"]
            record = model_to_post.with_context(**context).create(data)
        else:
            record = model_to_post.create(data)
        return record.id

    # This is for single record update
    @http.route(
        '/api/<string:model>/<int:rec_id>/',
        type='json', auth="user", methods=['PUT'], csrf=False)
    def put_model_record(self, model, rec_id, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on PUT request body"
            raise exceptions.ValidationError(msg)

        try:
            model_to_put = request.env[model]
        except KeyError:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)

        if "context" in post:
            # TODO: Handle error raised by `ensure_one`
            rec = model_to_put.with_context(**post["context"]) \
                .browse(rec_id).ensure_one()
        else:
            rec = model_to_put.browse(rec_id).ensure_one()

        # TODO: Handle data validation
        for field in data:
            if isinstance(data[field], dict):
                operations = []
                for operation in data[field]:
                    if operation == "push":
                        operations.extend(
                            (4, rec_id, _)
                            for rec_id
                            in data[field].get("push")
                        )
                    elif operation == "pop":
                        operations.extend(
                            (3, rec_id, _)
                            for rec_id
                            in data[field].get("pop")
                        )
                    elif operation == "delete":
                        operations.extend(
                            (2, rec_id, _)
                            for rec_id
                            in data[field].get("delete")
                        )
                    else:
                        data[field].pop(operation)  # Invalid operation

                data[field] = operations
            elif isinstance(data[field], list):
                data[field] = [(6, _, data[field])]  # Replace operation
            else:
                pass

        try:
            return rec.write(data)
        except Exception as e:
            # TODO: Return error message(e.msg) on a response
            return False

    # This is for bulk update
    @http.route(
        '/api/<string:model>/',
        type='json', auth="user", methods=['PUT'], csrf=False)
    def put_model_records(self, model, **post):
        try:
            data = post['data']
        except KeyError:
            msg = "`data` parameter is not found on PUT request body"
            raise exceptions.ValidationError(msg)

        try:
            model_to_put = request.env[model]
        except KeyError:
            msg = "The model `%s` does not exist." % model
            raise exceptions.ValidationError(msg)

        # TODO: Handle errors on filter
        filters = post["filter"]

        if "context" in post:
            recs = model_to_put.with_context(**post["context"]) \
                .search(filters)
        else:
            recs = model_to_put.search(filters)

        # TODO: Handle data validation
        for field in data:
            if isinstance(data[field], dict):
                operations = []
                for operation in data[field]:
                    if operation == "push":
                        operations.extend(
                            (4, rec_id, _)
                            for rec_id
                            in data[field].get("push")
                        )
                    elif operation == "pop":
                        operations.extend(
                            (3, rec_id, _)
                            for rec_id
                            in data[field].get("pop")
                        )
                    elif operation == "delete":
                        operations.extend(
                            (2, rec_id, _)
                            for rec_id in
                            data[field].get("delete")
                        )
                    else:
                        pass  # Invalid operation

                data[field] = operations
            elif isinstance(data[field], list):
                data[field] = [(6, _, data[field])]  # Replace operation
            else:
                pass

        if recs.exists():
            try:
                return recs.write(data)
            except Exception as e:
                # TODO: Return error message(e.msg) on a response
                return False
        else:
            # No records to update
            return True

    # This is for deleting one record
    @http.route(
        '/api/<string:model>/<int:rec_id>/',
        type='http', auth="user", methods=['DELETE'], csrf=False)
    def delete_model_record(self, model, rec_id, **post):
        try:
            model_to_del_rec = request.env[model]
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            res = error_response(e, msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        # TODO: Handle error raised by `ensure_one`
        rec = model_to_del_rec.browse(rec_id).ensure_one()

        try:
            is_deleted = rec.unlink()
            res = {
                "result": is_deleted
            }
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )
        except Exception as e:
            res = error_response(e, str(e))
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

    # This is for bulk deletion
    @http.route(
        '/api/<string:model>/',
        type='http', auth="user", methods=['DELETE'], csrf=False)
    def delete_model_records(self, model, **post):
        filters = json.loads(post["filter"])

        try:
            model_to_del_rec = request.env[model]
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            res = error_response(e, msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        # TODO: Handle error raised by `filters`
        recs = model_to_del_rec.search(filters)

        try:
            is_deleted = recs.unlink()
            res = {
                "result": is_deleted
            }
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )
        except Exception as e:
            res = error_response(e, str(e))
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

    @http.route(
        '/api/<string:model>/<int:rec_id>/<string:field>',
        type='http', auth="user", methods=['GET'], csrf=False)
    def get_binary_record(self, model, rec_id, field, **post):
        try:
            request.env[model]
        except KeyError as e:
            msg = "The model `%s` does not exist." % model
            res = error_response(e, msg)
            return http.Response(
                json.dumps(res),
                status=200,
                mimetype='application/json'
            )

        rec = request.env[model].browse(rec_id).ensure_one()
        if rec.exists():
            src = getattr(rec, field).decode("utf-8")
        else:
            src = False
        return http.Response(
            src
        )

    @http.route(
        '/journal/get_all_journal_details/',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def journal_details_api(self):
        # $journal_detail[] = array(
        #     'journal_no' = > $journal_value->journal_no, 'billing_name' = > $billing_name, 'amount' = > $journal_value->amount, 'total_debit_amount' = > $journal_value->total_debit_amount, 'total_credit_amount' = > $journal_value->total_credit_amount, 'journal_id' = > $journal_value->journal_id, 'tally_sync' = > $journal_value->tally_sync,
        # );

        # res = request.env['account.move'].search(
        #     [('move_type', '=', 'entry'), ('state', '!=', 'draft'),
        #      ('journal_id.type', '=', 'general')])
        # , ('journal_id.journal_type', '=', 'outbound')
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
             ('state', '!=', 'draft'), ('posted_before', '=', True),
             ('journal_id.type', 'in', ['general', 'cash', 'bank']),
             # ('payment_ids.is_internal_transfer', '=', True),  # 🔥 new condition
             ])

        # res = request.env['account.payment'].search(
        #     [('is_internal_transfer', '=', False)],
        #     limit=1
        # )

        # print(res)
        return_data = []
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            result = {}
            item = request.env['account.move.line'].search([('move_id', '=', data.id)])[0]
            billing_name = item.account_id.name
            if item.account_id.name == 'Debtors' or item.account_id.name == 'Creditors':
                # check if partner_id exist
                if item.partner_id is not None:
                    billing_name = item.partner_id.tally_mapper_name if item.partner_id.tally_mapper_name is not False else item.partner_id.name
            result['journal_no'] = data.name
            result['billing_name'] = billing_name  # 'Demo' #data.invoice_partner_display_name
            if data.state == 'cancel':
                result['billing_name'] = '<span style="color:red">PURGED</span>'
            result['amount'] = data.amount_total
            # result['total_debit_amount'] = data.amount_total
            # result['total_credit_amount'] = data.amount_total
            result['journal_id'] = data.id
            result['tally_sync'] = data.tally_sync
            result['tally_alter'] = data.tally_alter
            result['is_internal_transfer'] = 'mohammad'
            # result['tally_alter'] = 0
            return_data.append(result)

        return return_data

    @http.route(
        '/journal/get_journal_details/<int:rec_id>',
        type='json', auth='user', methods=["POST"], csrf=False, cors='*')
    def single_journal_details_api(self, rec_id):
        # $journal_item_bucket[] = array(
        #     'item_id' = > $journal_item->ledger_id,
        #     'item_name' = > $this->mdl_journal_item->get_ledger_name($journal_item->ledger_id), 'tally_ledger_name_mapper' = > $this->mdl_journal->get_tally_ledger_name($journal_item->ledger_id), 'ledger_description' = > $journal_item->ledger_description,
        #     'ppi_id' = > $journal_item->id,
        #     'item_amount' = > $journal_item->amount,
        #     'item_dr_cr' = > $journal_item->dr_cr,
        # );

        # res = request.env['account.move'].search([('id', '=', rec_id)])
        res = request.env['account.move'].search(
            ['|', ('tally_sync', '=', False), ('tally_alter', '=', True), ('move_type', '=', 'entry'),
             ('state', '!=', 'draft'), ('posted_before', '=', True),
             ('journal_id.type', 'in', ['general', 'cash', 'bank']), ('id', '=', rec_id)])
        journal_item_bucket = []
        journal_service_bucket = []
        item_ids = []
        ledger_mapper_details = []
        journal_item_bucket = []
        journal_data = []
        last_item_id = 0
        # account_move_lines = self.env['account.move.line'].search(
        # [('tax_line_id', '!=', None), ('move_id', '=', self.id)])
        # data = []
        is_cgst_sgst = False

        # data.append({'is_cgst_sgst':is_cgst_sgst})
        roundoff_amount = 0.00
        total_qty = 0.00
        transaction_type = {'bank': 'E-FUND TRANSFER', 'cash': 'CASH', 'cheque': 'CHEQUE'}
        res_config_settings = request.env['res.config.settings'].search([], order="id desc", limit=1)
        for data in res:
            if data.state == 'cancel':
                journal_data.append({
                    'journal_id': data.id,
                    'voucher_type': data.journal_id.tally_mapper_name,
                    'voucher_name': data.journal_id.tally_mapper_name,
                    'journal_date': data.date.strftime("%Y%m%d"),
                    'due_date': data.date.strftime("%Y%m%d"),
                    'journal_no': data.name,
                    'tally_sync': data.tally_sync,
                    'tally_alter': data.tally_alter,
                    'company_name': data.company_id.name,
                    'branch_name': 'Main Location',  # sale->branch_master()->tally_branch_name_mapper,
                    'address': '',
                    'state': '',
                    'city': '',
                    'country': '',
                })
            else:
                invoice_line_ids = request.env['account.move.line'].search([('move_id', '=', data.id)])
                # print(data.ref)
                # print(data.invoice_line_ids)
                # print(invoice_line_ids)
                # print('data.invoice_line_ids')
                # for item in data.invoice_line_ids:
                for item in invoice_line_ids:
                    l_data = {}
                    l_data['item_name'] = item.account_id.name
                    l_data['tally_ledger_name_mapper'] = item.account_id.name
                    if item.account_id.name == 'Debtors' or item.account_id.name == 'Creditors':
                        # check if partner_id exist
                        if item.partner_id is not None:
                            l_data[
                                'item_name'] = item.partner_id.tally_mapper_name if item.partner_id.tally_mapper_name is not False else item.partner_id.name
                            l_data[
                                'tally_ledger_name_mapper'] = item.partner_id.tally_mapper_name if item.partner_id.tally_mapper_name is not False else item.partner_id.name
                    l_data['item_id'] = item.id
                    l_data['ledger_description'] = item.name if item.name is not False else ''
                    item_amount = item.credit
                    item_dr_cr = 'CR'
                    if item.debit > 0.00:
                        item_amount = item.debit
                        item_dr_cr = 'DR'
                    l_data['item_amount'] = item_amount
                    l_data['item_dr_cr'] = item_dr_cr
                    journal_item_bucket.append(l_data)

                # address = str(res_original_inv.partner_id.street if res_original_inv.partner_id.street is not False else '') + '\n' + str(
                #     res_original_inv.partner_id.street2 if res_original_inv.partner_id.street2 is not False else '') + '\n' + str(
                #     res_original_inv.partner_id.zip if res_original_inv.partner_id.zip is not False else '') + '\n'

                # $journal_detail[] = array(
                #     'journal_id' = > $journal->journal_id,
                #     'is_manual' = > $is_manual,
                #     'voucher_name' = > $voucher_type,
                #     'journal_date' = > $journal_date_format,
                #     'journal_no' = > $journal->journal_no,
                #     'voucher_id' = > $journal->voucher_id,
                #     'item_amount' = > $journal->amount,
                #     'total_debit_amount' = > $journal->total_debit_amount,
                #     'total_credit_amount' = > $journal->total_credit_amount,
                #     'first_item_name' = > $this->mdl_journal->get_ledger_name($journal->ledger_id), 'tally_ledger_name_mapper' = > $this->mdl_journal->get_tally_ledger_name($journal->ledger_id), 'first_item_id' = > $journal->ledger_id,
                #     'journal_item' = > $journal_item_bucket,
                #     'narration' = > $journal->narration,
                #     'reference_no' = > $journal->reference_no,
                #     'due_date' = > $due_date_format,
                #     'company_name' = > $this->mdl_journal->get_tally_company_name_mapper($journal->company_id), 'state' = > $state,
                # );
                tally_ledger_name_mapper_final = data.invoice_line_ids[0].account_id.name
                if data.invoice_line_ids[0].account_id.name == 'Debtors' or data.invoice_line_ids[
                    0].account_id.name == 'Creditors':
                    # check if partner_id exist
                    if data.invoice_line_ids[0].partner_id is not None:
                        tally_ledger_name_mapper_final = data.invoice_line_ids[
                            0].partner_id.tally_mapper_name if data.invoice_line_ids[
                                                                   0].partner_id.tally_mapper_name is not False else \
                            data.invoice_line_ids[0].partner_id.namejournal_data.append({
                                'journal_id': data.id,
                                'voucher_type': data.journal_id.tally_mapper_name,
                                'voucher_name': data.journal_id.tally_mapper_name,
                                'journal_date': data.date.strftime("%Y%m%d"),
                                'journal_no': data.name,
                                'item_amount': data.amount_total,
                                'tally_ledger_name_mapper': tally_ledger_name_mapper_final,
                                'journal_item': journal_item_bucket,
                                'narration': data.narration if data.narration is not False else '',
                                'reference_no': data.ref if data.ref is not False else '',
                                'due_date': data.date.strftime("%Y%m%d"),
                                'company_name': data.company_id.name,
                                'state': data.company_id.partner_id.state_id.name,
                                'is_internal_transfer': data.is_internal_transfer,
                                # 'tally_sync': 0,
                                # 'tally_alter': 0,

                            })
        return journal_data
        # return ledger_mapper_details
