from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    part_no = fields.Char(string="Part No.")