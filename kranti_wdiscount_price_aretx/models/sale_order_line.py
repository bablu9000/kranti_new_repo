from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discounted_unit_price = fields.Float(
        string="Discounted Rate",
        compute="_compute_discounted_unit_price",
        digits="Product Price",
    )

    @api.depends("price_unit", "discount")
    def _compute_discounted_unit_price(self):
        for line in self:
            line.discounted_unit_price = (
                line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            )