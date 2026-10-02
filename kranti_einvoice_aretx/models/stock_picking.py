from odoo import models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    kppl_number = fields.Char(
        string="KPPL Order No.",
        related="sale_id.kppl_number",
        store=True,
        readonly=False,
        
    )