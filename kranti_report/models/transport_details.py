# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TransportDetails(models.Model):
	_name = 'transport.details'
	_description = 'Transport Details'

	name = fields.Char('Transport Name', required=True)
	transport_id = fields.Char('Transport ID')
