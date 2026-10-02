from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_delivery_label(self):
        self.ensure_one()
        return {
            'name': 'Print Delivery Label',
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            },
        }
