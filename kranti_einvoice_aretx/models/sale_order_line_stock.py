# from odoo import models
# from odoo.tools import float_compare


# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"

#     def _action_launch_stock_rule(
#         self,
#         *,
#         previous_product_uom_qty=False
#     ):

#         if self.env.context.get("skip_procurement"):
#             return True

#         precision = self.env[
#             "decimal.precision"
#         ].precision_get("Product Unit")

#         procurements = []

#         for line in self:

#             line = line.with_company(line.company_id)

#             if (
#                 line.state != "sale"
#                 or line.order_id.locked
#                 or line.product_id.type != "consu"
#             ):
#                 continue

#             qty = line._get_qty_procurement(
#                 previous_product_uom_qty
#             )

#             # USE CUSTOM TOTAL UNITS
#             product_qty = line.total_package_units - qty

#             if float_compare(
#                 product_qty,
#                 0.0,
#                 precision_digits=precision,
#             ) <= 0:
#                 continue

#             references = line.order_id.stock_reference_ids

#             if not references:
#                 self.env[
#                     "stock.reference"
#                 ].create(
#                     line._prepare_reference_vals()
#                 )

#             values = line._prepare_procurement_values()

#             procurements += line._create_procurements(
#                 product_qty,
#                 line.product_id.uom_id,
#                 values
#             )

#         if procurements:
#             self.env["stock.rule"].run(
#                 procurements
#             )

#         orders = self.mapped("order_id")

#         for order in orders:
#             pickings = order.picking_ids.filtered(
#                 lambda p: p.state not in (
#                     "cancel",
#                     "done",
#                 )
#             )

#             if pickings:
#                 pickings.action_confirm()

#         return True