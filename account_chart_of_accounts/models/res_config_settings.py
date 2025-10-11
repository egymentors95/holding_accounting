# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2021 (<http://www.exp-sa.com/>).
#
##############################################################################
from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    chart_account_length = fields.Integer(
        string='Chart of accounts length'
    )
    chart_account_padding = fields.Integer(
        string='Chart of accounts Padding'
    )
    useFiexedTree = fields.Boolean(
        string='Use Fixed Length Chart of accounts'
    )
    automticAccountsCodes = fields.Boolean(
        string='Automaticly Generate Accounts Codes'
    )
    parent_bank_cash_account_id = fields.Many2one('account.account')



    @api.model
    def setting_chart_of_accounts_action(self):
        """ Called by the 'Chart of Accounts' button of the setup bar."""
        company = self.env.company
        company.sudo().set_onboarding_step_done('account_setup_coa_state')

        # If an opening move has already been posted, we open the tree view showing all the accounts
        if company.opening_move_posted():
            return 'account.action_account_form'

        # Otherwise, we create the opening move
        company.create_op_move_if_non_existant()

        # Then, we open will open a custom tree view allowing to edit opening balances of the account
        view_id = self.env.ref('account.init_accounts_tree').id
        # Hide the current year earnings account as it is automatically computed
        domain = [('user_type_id', 'not in', [self.env.ref('account.data_unaffected_earnings').id,
                                              self.env.ref('account_chart_of_accounts.data_account_type_view').id]),
                  ('company_id', '=', company.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Chart of Accounts'),
            'res_model': 'account.account',
            'view_mode': 'tree',
            'limit': 99999999,
            'search_view_id': self.env.ref('account.view_account_search').id,
            'views': [[view_id, 'list']],
            'domain': domain,
        }


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    chart_account_length = fields.Integer(
        related='company_id.chart_account_length',
        readonly=False
    )
    chart_account_padding = fields.Integer(
        related='company_id.chart_account_padding',
        readonly=False
    )
    useFiexedTree = fields.Boolean(
        related='company_id.useFiexedTree',
        readonly=False
    )
    automticAccountsCodes = fields.Boolean(
        related='company_id.automticAccountsCodes',
        readonly=False
    )
    bank_account_code_prefix = fields.Char(
        string='Bank Prefix',
        related='company_id.bank_account_code_prefix',
        readonly=False
    )
    cash_account_code_prefix = fields.Char(
        string='Cash Prefix',
        related='company_id.cash_account_code_prefix',
        readonly=False
    )
