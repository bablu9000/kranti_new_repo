from odoo import api, fields, models


class EwaybillTransporterCustomer(models.Model):
    _name = "ewaybill.transporter.customer"
    _description = "Transporter Customer E-Waybill Distance"
    _rec_name = "customer_id"

    transporter_id = fields.Many2one(
        "res.partner",
        string="Transporter",
        required=True,
        ondelete="cascade",
        domain="[('category_id.name', '=', 'Transporter')]",
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        ondelete="cascade",
    )

    last_distance = fields.Integer(
        string="Last Distance (KM)",
        required=True,
        default=0,
    )

    _transporter_customer_unique = models.Constraint(
        "UNIQUE(transporter_id, customer_id)",
        "A distance record already exists for this transporter and customer.",
    )