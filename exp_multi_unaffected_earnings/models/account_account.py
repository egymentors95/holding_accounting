# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    earning_account_id = fields.Many2one(
        comodel_name = 'account.account',
        domain=lambda self: self._earning_account_domain()
    )

    def _earning_account_domain(self):
        return [('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)]


    @api.constrains('user_type_id')
    def _check_user_type_id_unique_current_year_earning(self):
        pass