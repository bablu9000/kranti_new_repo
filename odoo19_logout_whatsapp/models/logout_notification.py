from odoo import fields, models


class LogoutNotification(models.Model):
    _name = "logout.whatsapp.notification"
    _description = "Odoo Logout WhatsApp Notification"

    name = fields.Char(required=True, default="Odoo Logout Notification")
    phone = fields.Char(required=True)
    message = fields.Text()
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    logout_datetime = fields.Datetime(required=True)
    ip_address = fields.Char()
    company_id = fields.Many2one("res.company")
