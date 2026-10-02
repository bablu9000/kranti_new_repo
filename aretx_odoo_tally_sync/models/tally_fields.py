from odoo import api, fields, models


class VoucherTally(models.Model):
    _inherit = 'account.move'
    tally_sync = fields.Boolean(string="Tally Sync", default=False)
    tally_alter = fields.Boolean(string="Tally Alter", default=False)
    tally_sync_date = fields.Datetime('Tally Sync Date')
    #  temp fields
    whatsapp_sent = fields.Char(index=True)
    booking_name = fields.Char(index=True)
    kppl_number = fields.Char(index=True)
    # transporter_id = fields.Char(index=True)
    lr_no = fields.Char(index=True)
    lr_date = fields.Char(index=True)
    boxes = fields.Char(index=True)
    bags = fields.Char(index=True)
    total = fields.Float()

    #  temp fields

    def write(self, vals):
        if 'invoice_line_ids' in vals:
            for move in self:
                move.write({
                    'tally_sync': False,
                    'tally_alter': True,
                })
            # Remove those custom fields from vals so they don't get re-applied again globally
            vals.pop('tally_sync', None)
            vals.pop('tally_alter', None)

        return super().write(vals)

def _move_autocomplete_invoice_lines_write(self, vals):

        # ac_move = self.env['account.move'].search([('id', '=', self._ids)])
        #print('Mohammad--------------------')
        # print(vals)
        # print('vals1--------------------')
        # if 'tally_sync_date' not in vals and 'tally_sync' in vals and vals['tally_sync'] is True and 'tally_alter' in vals and vals['tally_alter'] is False:
        # if vals['tally_sync'] is True and vals['tally_alter'] is False:
        # if ac_move.tally_sync is True and ac_move.tally_alter is False:
        if 'tally_sync_date' not in vals and len(vals) > 0:
            # print('vals--------------------')
            # print(vals)
            # print('vals--------------------')
            vals['tally_sync'] = False
            vals['tally_alter'] = True
            for invoice in self:
                invoice_new_update = invoice.with_context(default_move_type=invoice.move_type,
                                                          default_journal_id=invoice.journal_id.id).new(origin=invoice)
                invoice_new_update.update(vals)
                # print('vals2--------------------')
                # print(vals)
                # print('vals2--------------------')
        # res = super(VoucherTally, self).write(vals)
        # return True




class ProductTemplateTally(models.Model):
    _inherit = 'product.template'

    tally_sync = fields.Boolean(string="Tally Sync", default=False)
    tally_alter = fields.Boolean(string="Tally Alter", default=False)
    tally_sync_date = fields.Datetime('Tally Sync Date')

    def write(self, vals):
        product = self.env['product.product'].search([('product_tmpl_id', '=', self._ids)])
        if len(product) == 1 and product.tally_sync is True and product.tally_alter is False:
            product.write({'tally_sync': False, 'tally_alter': True})
        if 'uom_id' in vals or 'uom_po_id' in vals:
            uom_id = self.env['uom.uom'].browse(vals.get('uom_id')) or self.uom_id
            uom_po_id = self.env['uom.uom'].browse(vals.get('uom_po_id')) or self.uom_po_id
            if uom_id and uom_po_id and uom_id.category_id != uom_po_id.category_id:
                vals['uom_po_id'] = uom_id.id
        res = super(ProductTemplateTally, self).write(vals)
        if 'attribute_line_ids' in vals or (vals.get('active') and len(self.product_variant_ids) == 0):
            self._create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        return res


class CustomerTally(models.Model):
    _inherit = 'res.partner'
    tally_sync = fields.Boolean(string="Tally Sync", default=False)
    tally_alter = fields.Boolean(string="Tally Alter", default=False)
    tally_sync_date = fields.Datetime('Tally Sync Date')

    def write(self, vals):
        for rec in self:
            customer = self.env['res.partner'].search([('id', '=', rec.id)])
            if len(customer) == 1 and customer.tally_sync is True and customer.tally_alter is False:
                vals['tally_sync'] = False
                vals['tally_alter'] = True
        res = super(CustomerTally, self).write(vals)
        return res


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    tally_mapper_name = fields.Char(
        string='Tally Mapper Name',
        help='Name of the mapper in Tally for this Journal'
    )
