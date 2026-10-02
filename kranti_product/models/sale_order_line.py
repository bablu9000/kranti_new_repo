from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_sale_order_line_multiline_description_sale(self):
        description = super()._get_sale_order_line_multiline_description_sale()
        uom_ids = self.product_id.product_tmpl_id.uom_ids
        if uom_ids:
            uom_names = ', '.join(uom_ids.mapped('name'))
            description += '\n' + f'Packagings: {uom_names}'
        return description
