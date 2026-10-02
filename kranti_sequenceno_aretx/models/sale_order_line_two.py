from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_no = fields.Integer(
        string="Sr. No.",
        compute="_compute_line_no",
        store=False,
    )

    @api.depends("order_id.order_line.sequence")
    def _compute_line_no(self):
        # Default for all records
        for line in self:
            line.line_no = 0

        # Assign numbering according to sequence
        for order in self.mapped("order_id"):
            lines = order.order_line.sorted(key=lambda l: l.sequence)
            for index, line in enumerate(lines, start=1):
                line.line_no = index