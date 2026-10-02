from odoo import api, fields, models


class ProductLabelWizard(models.TransientModel):
    _name = 'product.label.wizard'
    _description = 'Product Label Print Wizard'

    product_template_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        readonly=True,
    )
    # REMOVED: lot_id no longer needed — all data now comes from product.template
    # lot_id = fields.Many2one(
    #     'stock.lot',
    #     string='Lot / Serial Number',
    #     domain="[('product_id.product_tmpl_id', '=', product_template_id)]",
    #     required=True,
    # )
    batch_number = fields.Char(string='Batch Number', required=True)
    # ADDED: computed field to restrict packaging choices to product's UoMs
    allowed_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_allowed_uom_ids',
    )
    # CHANGED: was Many2many — now Many2one for single packaging selection
    # packaging_ids = fields.Many2many(
    #     'uom.uom',
    #     string='Packagings',
    # )
    # CHANGED: added domain to restrict to product's UoMs
    packaging_id = fields.Many2one(
        'uom.uom',
        string='Packaging',
        domain="[('id', 'in', allowed_uom_ids)]",
    )

    @api.depends('product_template_id')
    def _compute_allowed_uom_ids(self):
        for wizard in self:
            if wizard.product_template_id:
                wizard.allowed_uom_ids = wizard.product_template_id.uom_ids
            else:
                wizard.allowed_uom_ids = False

    def action_print_label(self):
        self.ensure_one()
        return self.env.ref(
            'kranti_product.action_report_product_label'
        ).report_action(self)
