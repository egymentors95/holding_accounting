# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo.osv import expression

from odoo import fields, models, api, _


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    _parent_name = "parent_id"
    _parent_store = True

    parent_id = fields.Many2one('account.analytic.account', )

    parent_path = fields.Char(
        index=True
    )
    crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'analytic_account_id', 'Budget Lines')

    @api.depends('line_ids.amount')
    def _compute_debit_credit_balance(self):
        Curr = self.env['res.currency']
        analytic_line_obj = self.env['account.analytic.line']
        domain = [('account_id', 'in', self.ids),
                  ('company_id', 'in', [False] + self.env.companies.ids)
                  ]
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))
        if self._context.get('tag_ids'):
            tag_domain = expression.OR([[('tag_ids', 'in', [tag])] for tag in self._context['tag_ids']])
            domain = expression.AND([domain, tag_domain])
        user_currency = self.env.company.currency_id
        credit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '>=', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_credit = defaultdict(float)
        for l in credit_groups:
            data_credit[l['account_id'][0]] += Curr.browse(l['currency_id'][0])._convert(
                l['amount'], user_currency, self.env.company, fields.Date.today())

        debit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '<', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )

        data_debit = defaultdict(float)
        for l in debit_groups:
            data_debit[l['account_id'][0]] += Curr.browse(l['currency_id'][0])._convert(
                l['amount'], user_currency, self.env.company, fields.Date.today())
        for account in self:
            analytic_ids = self.env['account.analytic.account'].search(
                ['|', ('id', '=', account.id), ('parent_id', 'like', account.id)])
            debit = 0
            credit = 0
            for analytic in analytic_ids:
                debit += abs(data_debit.get(analytic.id, 0.0))
                credit += data_credit.get(analytic.id, 0.0)
            account.debit = debit
            account.credit = credit
            account.balance = account.credit - account.debit
# def copy(self, default=None):
    #     default = default or {}
    #     res = super(AccountAnalyticAccount, self).copy(default)
    #     for line in self.crossovered_budget_line:
    #         line.copy({'analytic_account_id': res.id})
    #     return res
