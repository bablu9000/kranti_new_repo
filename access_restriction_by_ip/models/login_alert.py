# -*- coding: utf-8 -*-

from odoo import fields, models


class LoginAlert(models.Model):
    _name = 'odoo.login.alert'
    _description = 'Odoo Login Alert'
    _order = 'login_datetime desc'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=True,
        default='Login Alert',
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        readonly=True,
        ondelete='cascade',
    )

    login = fields.Char(
        string='Login',
        readonly=True,
    )

    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
    )

    login_datetime = fields.Datetime(
        string='Login Time',
        readonly=True,
    )

    phone = fields.Char(
        string='Phone',
        readonly=True,
    )

    status = fields.Selection(
        [
            ('success', 'Successful Login'),
        ],
        string='Status',
        default='success',
        readonly=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        default=lambda self: self.env.company,
    )

    # def name_get(self):
    #     result = []

    #     for record in self:
    #         user_name = (
    #             record.user_id.name
    #             or record.login
    #             or 'User'
    #         )

    #         login_time = (
    #             str(record.login_datetime)
    #             if record.login_datetime
    #             else ''
    #         )

    #         result.append(
    #             (
    #                 record.id,
    #                 '%s - %s' % (
    #                     user_name,
    #                     login_time,
    #                 ),
    #             )
    #         )

    #     return result