from odoo import models, fields, api


class JournalType(models.Model):
    _name = 'account.journal.type'
    _description = 'Journal Type'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)