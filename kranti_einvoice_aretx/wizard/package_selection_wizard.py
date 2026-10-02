from odoo import fields, models, api

class PackageSelectionWizard(models.TransientModel):
    _name = "package.selection.wizard"
    _description = "Package Selection Wizard"

    sale_line_id = fields.Many2one(
        "sale.order.line",
        required=True
    )

    line_ids = fields.One2many(
        "package.selection.wizard.line",
        "wizard_id",
        string="Packages",
    )

    def action_save(self):
        self.ensure_one()

        sale_line = self.sale_line_id

        sale_line.package_line_ids.unlink()

        vals = []

        for line in self.line_ids:
            vals.append(
                (
                    0,
                    0,
                    {
                        "package_id": line.package_id.id,
                        "quantity": line.quantity,
                    },
                )
            )

        sale_line.package_line_ids = vals

        total_units = sum(self.line_ids.mapped("unit_qty"))

        sale_line.product_uom_qty = total_units
        sale_line.product_uom_id = sale_line.product_id.uom_id

        # Refresh the description
        sale_line._update_package_description()

        return {
            "type": "ir.actions.act_window_close",
        }
        
        
class PackageSelectionWizardLine(models.TransientModel):
    _name = "package.selection.wizard.line"
    _description = "Package Selection Wizard Line"

    wizard_id = fields.Many2one(
        "package.selection.wizard",
        ondelete="cascade",
        required=True,
    )

    
    allowed_uom_ids = fields.Many2many(
        "uom.uom",
        compute="_compute_allowed_uom_ids",
    )

    package_id = fields.Many2one(
        "uom.uom",
        string="Package",
        required=True,
        domain="[('id', 'in', allowed_uom_ids)]",
    )

    @api.depends("wizard_id.sale_line_id.product_id")
    def _compute_allowed_uom_ids(self):
        for rec in self:
            product = rec.wizard_id.sale_line_id.product_id
            rec.allowed_uom_ids = product.product_tmpl_id.uom_ids

    quantity = fields.Integer(
        string="Box/Bag",
        default=1.0,
    )

    unit_qty = fields.Integer(
        string="Quantity",
        compute = "_compute_unit_qty"
    )

    @api.depends("package_id.factor", "quantity")
    def _compute_unit_qty(self):
        for rec in self:
            rec.unit_qty = rec.quantity * rec.package_id.factor


    