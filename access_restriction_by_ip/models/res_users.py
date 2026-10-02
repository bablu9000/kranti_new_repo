# -*- coding: utf-8 -*-
from odoo import fields, models
import socket

class ResUsersInherit(models.Model):
    """Inherited res_users for adding new field allowed ip_ids"""
    _inherit = 'res.users'

    allowed_ip_ids = fields.One2many('allowed.ips', 'user_ip_id',
                                     string='IP Address',
                                     help="Allowed ip addresses for the user.")
    current_ip = fields.Char(string='Current IP')

    def action_check_current_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address=s.getsockname()[0]
        self.current_ip = ip_address
        s.close()
        