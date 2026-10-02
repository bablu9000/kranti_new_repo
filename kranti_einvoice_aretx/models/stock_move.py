from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends("sale_line_id")
    def _compute_description_picking(self):
        super()._compute_description_picking()

        for move in self:
            if (
                move.sale_line_id
                and not move.description_picking_manual
            ):
                description = move.sale_line_id.name

                product_name = move.product_id.display_name

                if description.startswith(product_name):
                    description = description[len(product_name):].lstrip()

                move.description_picking = description