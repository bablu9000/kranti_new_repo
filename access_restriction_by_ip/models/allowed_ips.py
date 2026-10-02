# -*- coding: utf-8 -*-
from odoo import fields, models


class AllowedIPs(models.Model):
    """Class for the model allowed_ips. Contains fields for record users and
    their Allowed IPs."""
    _name = 'allowed.ips'
    _description = "Allowed IPs"

    user_ip_id = fields.Many2one('res.users', string='User',
                                 help='User associated with the allowed IP')
    ip_address = fields.Char(string='Allowed IP', help='The allowed IP address'
                                                       ' for the User.')
