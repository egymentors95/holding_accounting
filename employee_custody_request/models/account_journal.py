from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class AccountJournalInherit(models.Model):
    _inherit = 'account.journal'

    custody_journal = fields.Boolean(
        string='Custody Journal',
        default=False,
        help='Check this box if this journal is used for custody transactions'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help='Partner associated with this journal'
    )


    @api.onchange('custody_journal')
    def _onchange_custody_journal(self):
        if not self.custody_journal:
            return {
                'domain': {'default_account_id': []}
            }
        else:
            return {
                'domain': {
                    'default_account_id': [('user_type_id.type', '=', 'receivable')]
                }
            }

    @api.constrains('custody_journal', 'default_account_id')
    def _check_custody_account_type(self):
        for record in self:
            if record.custody_journal and record.default_account_id:
                if record.default_account_id.user_type_id.type != 'receivable':
                    raise ValidationError(_('You must select an account of type "Debit" for the Advances Ledger'))