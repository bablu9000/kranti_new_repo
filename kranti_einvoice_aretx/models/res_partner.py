from odoo import models, fields



class ResPartner(models.Model):
    _inherit = "res.partner"

    transporter_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_transporter_rel",
        column1="partner_id",
        column2="transporter_id",
        string="Transporters",
        domain="[('category_id.name','=','Transporter')]",
    )

    default_transporter_id = fields.Many2one(
        "res.partner",
        string="Default Transporter",
        domain="[('category_id.name','=','Transporter')]",
    )

    booking_name = fields.Char(string="Booking Name")

