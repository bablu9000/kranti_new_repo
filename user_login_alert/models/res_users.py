# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    """Inherits 'res.users' to add fields"""
    _inherit = 'res.users'

    last_logged_ip = fields.Char(string='IP', help="User lastly login Ip "
                                                   "address")
    last_logged_browser = fields.Char(string='Browser',
                                      help="User lastly login browser")
    last_logged_os = fields.Char(string='OS',
                                 help="User lastly login Operating system")
