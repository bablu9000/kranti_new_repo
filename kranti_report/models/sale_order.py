# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    udyam = fields.Char(string="UDYAM No")


class ResCompany(models.Model):
    _inherit = 'res.partner'

    msme = fields.Char(string="MSME No")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    transport_id = fields.Many2one('transport.details', string="Transport")
    vehicle = fields.Char(string="Vehicle No")
    lr = fields.Char(string="LR No")
    lr_date = fields.Datetime(string="LR Date")
    package = fields.Char(string="No Of Packages")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    box_qty = fields.Float(string="Box Qty", default=1)
    box_product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Package",
        compute='_compute_product_uom_id',
        domain='[("id", "in", allowed_uom_ids)]',
        store=True, readonly=False, precompute=True, ondelete='restrict')

    @api.onchange('box_product_uom_id', 'box_qty')
    def compute_pack_qty(self):
        for rec in self:
            if rec.box_product_uom_id and rec.box_qty:
                rec.product_uom_qty = rec.box_product_uom_id.relative_factor * rec.box_qty
