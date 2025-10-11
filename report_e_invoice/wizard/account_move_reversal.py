# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
   
    _inherit = 'account.move.reversal'

    
    selection_reason = fields.Selection(
        string='Reason',
        selection=[('edit_stop', 'Edit Or Stop'), ('change_complete_edit', 'Change Or complete Edit'),('edit_amount', 'Edit Amount'),('refund_goods', 'Refund Goods')]
    )
    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        
        res['reversal_reason'] = self.reason
        res['selection_reason'] = self.selection_reason
        return res

    # def _prepare_default_reversal(self, move):
    #     reverse_date = self.date if self.date_mode == 'custom' else move.date
    #     return {
    #         'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason)
    #         if self.reason
    #         else _('Reversal of: %s', move.name),
    #         'date': reverse_date,
    #         'reversal_reason': self.reason,
    #         'selection_reason': self.selection_reason,
    #         'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
    #         'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
    #         'invoice_payment_term_id': None,
    #         'invoice_user_id': move.invoice_user_id.id,
    #         'auto_post': True if reverse_date > fields.Date.context_today(self) else False,
    #     }
