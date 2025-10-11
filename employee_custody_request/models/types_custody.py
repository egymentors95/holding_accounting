from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CustodyTypes(models.Model):
    _name = 'custody.types'
    _description = 'Custody Types'
    _rec_name = 'name'

    name = fields.Char(
        string='Custody Type Name',
        required=True,
        help='Name of the custody type'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('custody_journal', '=', True)]",
        help='Select the journal associated with this type of custody'
    )

    max_custody_amount = fields.Float(
        string='Maximum Custody Amount',
        digits=(16, 2),
        required=True,
        help='The maximum amount allowed for this type of custody'
    )

    @api.constrains('max_custody_amount')
    def _check_max_custody_amount(self):
        for record in self:
            if record.max_custody_amount <= 0:
                raise ValidationError(_('The maximum custody amount must be greater than zero.'))
