from odoo import models, fields, api

class SaleOrderLinePackage(models.Model):
    _name="sale.order.line.package"
    _description="Sale Order Line Package"

    sale_line_id = fields.Many2one(
        "sale.order.line",
        required=True,
        ondelete="cascade"
    )
    package_id = fields.Many2one(
        "uom.uom",
        required=True,
        string="Package",
        domain="[('product_id', '='), sale_line_id.product_id]"
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits="Product Unit of Measure"
    )
    unit_qty = fields.Float(
        string="Units",
        compute = "_compute_unit_qty",
        store=True,
        digits="Product Unit of Measure"
    )

    @api.depends("package_id.factor", "quantity")
    def _compute_unit_qty(self):
        for rec in self:
            rec.unit_qty = rec.quantity * rec.package_id.factor
