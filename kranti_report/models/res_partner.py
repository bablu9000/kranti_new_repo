# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    transport_id = fields.Many2one(
        comodel_name='transport.details',
        string='Transport',
    )
