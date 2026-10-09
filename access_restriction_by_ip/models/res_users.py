# -*- coding: utf-8 -*-
from odoo import fields, models
import socket
from odoo.http import request

class ResUsersInherit(models.Model):
    """Inherited res_users for adding new field allowed ip_ids"""
    _inherit = 'res.users'

    allowed_ip_ids = fields.One2many('allowed.ips', 'user_ip_id',
                                     string='IP Address',
                                     help="Allowed ip addresses for the user.")
    current_ip = fields.Char(string='Current IP')
    login_time = fields.Float(string='Login Time')
    logout_time = fields.Float(string='Logout Time')
    current_time = fields.Datetime(string='Current Time')

    def action_check_current_ip(self):
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect(("8.8.8.8", 80))
        # ip_address=s.getsockname()[0]
        # self.current_ip = ip_address
        # s.close()
        # self.current_ip = request.httprequest.remote_addr

        # record.write({'current_ip' :record._get_client_ip()})

        http_request = request.httprequest
        forwarded_for = http_request.headers.get(
            'X-Forwarded-For'
        )

        real_ip = http_request.headers.get(
            'X-Real-IP'
        )
        client_ip = False
        if forwarded_for:
            client_ip = (
                forwarded_for
                .split(',')[0]
                .strip()
            )

            # if client_ip:
            #     client_ip = client_ip

        # ----------------------------------------------------------
        # X-Real-IP
        # ----------------------------------------------------------


        elif real_ip and client_ip == False:
            client_ip = real_ip.strip()
        else:
            client_ip = http_request.remote_addr
        self.current_ip = client_ip
        self.current_time = fields.Datetime.now()
        