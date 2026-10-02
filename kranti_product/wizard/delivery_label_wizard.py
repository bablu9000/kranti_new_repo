from odoo import api, fields, models


class DeliveryLabelWizard(models.TransientModel):
    _name = 'delivery.label.wizard'
    _description = 'Delivery Label Print Wizard'

    picking_id = fields.Many2one('stock.picking', string='Delivery', required=True, readonly=True)
    order_no = fields.Char(string='Order No', readonly=True)
    transport_name = fields.Char(string='Transport Name', readonly=True)
    total_carton = fields.Char(string='Total Carton', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.picking':
            picking = self.env['stock.picking'].browse(self.env.context['active_id'])
            sale_order = picking.move_ids.sale_line_id.order_id[:1]
            res['order_no'] = sale_order.name or picking.origin or ''
            # res['transport_name'] = picking.partner_id.name
            res['transport_name'] = sale_order.transporter_id.name or False
        return res

    def action_print_delivery_label(self):
        self.ensure_one()
        return self.env.ref('kranti_product.action_report_delivery_label').report_action(self)
