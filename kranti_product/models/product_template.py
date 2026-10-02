from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    size = fields.Char(string="Size")
    product_label = fields.Char(string="Label")

    def action_print_product_label(self):
        self.ensure_one()
        return {
            'name': 'Print Product Label',
            'type': 'ir.actions.act_window',
            'res_model': 'product.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_template_id': self.id,
                # REMOVED: no default needed — packaging_id is now single selection, user picks manually
                # 'default_packaging_ids': [(6, 0, self.uom_ids.ids)],
            },
        }