# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    seq = fields.Char(string="Sequence", copy=False)

    def action_post(self):
        for move in self:
            if not move.seq:
                move.seq = self.env['ir.sequence'].next_by_code('account.move')
        return super(AccountMove, self).action_post()
