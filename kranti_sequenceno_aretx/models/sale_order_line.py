from odoo import models, fields,api
from odoo.osv import expression
from odoo.exceptions import UserError

# #mohammad
# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     line_no = fields.Integer(
#         string="Line #",
#         compute="_compute_line_no",
#         store=False
#     )
#
#     @api.depends('order_id.order_line')
#     def _compute_line_no(self):
#         for order in self.mapped('order_id'):
#             for index, line in enumerate(order.order_line, start=1):
#                 line.line_no = index


#mohammad
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    line_no = fields.Integer(
        string="Line #",
        compute="_compute_line_no",
        store=False
    )

    @api.depends('move_id.invoice_line_ids')
    def _compute_line_no(self):
        # Step 1: assign default to ALL records
        for line in self:
            line.line_no = 0

        # Step 2: assign proper numbering only for invoice lines
        for move in self.mapped('move_id'):
            lines = move.invoice_line_ids.sorted(key=lambda l: l.sequence)
            for index, line in enumerate(lines, start=1):
                line.line_no = index
#
# class PurchaseOrderLine(models.Model):
#     _inherit = 'purchase.order.line'
#
#     line_no = fields.Integer(
#         string="Line #",
#         compute="_compute_line_no",
#         store=False
#     )
#
#     @api.depends('order_id.order_line')
#     def _compute_line_no(self):
#         # Default for all
#         for line in self:
#             line.line_no = 0
#
#         # Assign sequence
#         for order in self.mapped('order_id'):
#             lines = order.order_line.sorted(key=lambda l: l.sequence)
#             for index, line in enumerate(lines, start=1):
#                 line.line_no = index