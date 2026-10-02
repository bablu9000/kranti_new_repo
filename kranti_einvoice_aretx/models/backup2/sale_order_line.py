from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    total_pkgs = fields.Float(
        string="Total Packages",
        compute="_compute_total_pkgs",
        store=True,
    )

    package_action = fields.Char(
        string="Packages",
        compute="_compute_package_action",
    )

    package_line_ids = fields.One2many(
        "sale.order.line.package",
        "sale_line_id",
        string="Packages",
    )

    @api.depends("package_line_ids.quantity")
    def _compute_total_pkgs(self):
        for line in self:
            line.total_pkgs = sum(line.package_line_ids.mapped("quantity"))

    @api.depends("package_line_ids")
    def _compute_package_action(self):
        for line in self:
            line.package_action = "Packages"

    def action_open_package_wizard(self):
        self.ensure_one()

        if self.package_line_ids:
            line_vals = [
                (
                    0,
                    0,
                    {
                        "package_id": line.package_id.id,
                        "quantity": line.quantity,
                        "unit_qty": line.unit_qty,
                    
                    },
                )
                for line in self.package_line_ids
            ]
        else:
            line_vals = [
                (
                    0,
                    0,
                    {
                        "package_id": self.product_uom_id.id,
                        "quantity": self.product_uom_qty,
                    },
                )
            ]

        wizard = self.env["package.selection.wizard"].create(
            {
                "sale_line_id": self.id,
                "line_ids": line_vals,
            }
        )

        return {
            "name": "Packages",
            "type": "ir.actions.act_window",
            "res_model": "package.selection.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "kranti_einvoice_aretx.view_package_selection_wizard_form"
            ).id,
            "res_id": wizard.id,
            "target": "new",
        }

    def _get_sale_order_line_multiline_description_sale(self):
        description = super()._get_sale_order_line_multiline_description_sale()

        # Remove an existing packaging block if present
        if "Packagings:" in description:
            description = description.split("Packagings:")[0].rstrip()

        if self.package_line_ids:
            description += "\nPackagings:"
            for line in self.package_line_ids:
                description += f"\n{line.package_id.name}: {line.package_id.factor} x {line.quantity:g} = {line.unit_qty:g},"

        return description

    def _update_package_description(self):
        """
        Refresh the SO line description after editing packages.
        """
        for line in self:
            line.name = line._get_sale_order_line_multiline_description_sale()
    # ........................................................

    def _get_package_description(self):
        """
        Returns the packaging description.
        """
        self.ensure_one()

        if not self.package_line_ids:
            return ""

        description = "\nPackagings:"

        for line in self.package_line_ids:
            description += f"\n{line.package_id.name}: {line.package_id.factor} x {line.quantity:g} = {line.unit_qty:g},"

        return description

    
    
