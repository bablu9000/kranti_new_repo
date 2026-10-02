from odoo import api, fields, models



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_aretx_product_tally = fields.Boolean(string="Product Tally")
    module_aretx_customer_tally = fields.Boolean(string="Customer Tally")


    def execute(self):
        res = super().execute()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                # 'title': "Settings have been saved successfully.",
                'message': "Settings have been saved successfully.",
                'sticky': False,
                'type': 'info',  # types: success, warning, danger, info
            }
        }
