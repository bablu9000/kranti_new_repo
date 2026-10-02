from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    bank_branch = fields.Char("Bank Branch")