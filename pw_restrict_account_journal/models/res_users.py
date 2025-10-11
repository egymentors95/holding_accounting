# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    journal_ids = fields.Many2many('account.journal')
    show_journal = fields.Boolean(compute='_compute_show_journal')

    def _compute_show_journal(self):
        for user in self:
            if user.has_group('pw_restrict_account_journal.pw_group_journal_restriction'):
                user.show_journal = True
            else:
                user.show_journal = False

    def write(self, vals):
        if 'journal_ids' in vals:
            self.env['ir.rule'].clear_caches()
        return super(ResUsers, self).write(vals)
