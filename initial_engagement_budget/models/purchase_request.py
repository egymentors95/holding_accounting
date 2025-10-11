# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    state = fields.Selection(
        selection_add=[('wait_for_send', 'Wait For Sent'),
                       ('initial', 'Initial Engagement')],
        default="draft",
        tracking=True
    )
    state_a = fields.Selection(related='state', tracking=False)
    state_b = fields.Selection(related='state', tracking=False)

    initial_engagement_activate = fields.Boolean(compute='_check_initial_engagement_activate', store=True,
                                                 default=False)
    total_amount = fields.Monetary(string="Total", compute="_compute_total_amount",
                                   currency_field='company_currency_id', store=True)
    company_currency_id = fields.Many2one("res.currency", string="Currency", related="company_id.currency_id",
                                          readonly=True)

    @api.depends('line_ids', 'line_ids.line_total')
    def _compute_total_amount(self):
        for request in self:
            request.total_amount = sum(line.line_total for line in request.line_ids)

    def action_skip_budget(self):
        self.state = 'waiting'

    @api.depends('name', 'date', 'department_id', 'state')
    def _check_initial_engagement_activate(self):
        for rec in self:
            rec.initial_engagement_activate = rec.company_id.activate_initial_engagement

    def action_confirm(self) -> Optional[bool]:
        if self.env.user.company_id.activate_initial_engagement:
            for rec in self:
                rec.state = 'wait_for_send'
            return
        return super(PurchaseRequest, self).action_confirm()

    def initial_engagement(self) -> None:
        for rec in self:
            rec.action_budget_initial()
            rec.state = 'initial'

    def action_refuse(self):
        res = super(PurchaseRequest, self).action_refuse()
        for rec in self:
            budget_confs = self.env['budget.confirmation'].search([('request_id', '=', rec.id)])
            budget_confs.write({'state': 'cancel'})
        return res

    def action_budget_initial(self):
        confirmation_lines = []
        amount = 0
        total_amount = sum(line.line_total for line in self.line_ids)
        if total_amount <= 0:
            raise ValidationError(_("Total Amount MUST be greater than 0 !!!"))
        if self.use_analytic:
            analytic_account = self.account_analytic_id
        else:
            analytic_account = self.department_id.analytic_account_id

        for order in self:
            for rec in order.line_ids:
                account_id = rec.product_id.property_account_expense_id and rec.product_id.property_account_expense_id or rec.product_id.categ_id.property_account_expense_categ_id
                if not account_id:
                    raise ValidationError(
                        _("This product has no expense account") + ': {}'.format(rec.product_id.name))

                budget_post = self.env['account.budget.post'].search([]).filtered(lambda x: account_id in x.account_ids)
                if len(budget_post.ids) > 1:
                    raise ValidationError(
                        _("The Expense account %s is assigned to more than one budget position %s") % (
                            account_id.name, [x.name for x in budget_post]))
                budget_lines = self.env['crossovered.budget.lines'].search(
                    [('analytic_account_id', '=', analytic_account.id),
                     ('general_budget_id', 'in', budget_post.ids),
                     ('crossovered_budget_id.state', '=', 'done'),
                     ('crossovered_budget_id.date_from', '<=', self.date),
                     ('crossovered_budget_id.date_to', '>=', self.date)])

                budget_line = budget_lines.mapped('crossovered_budget_id')
                if len(budget_line) > 1:
                    self.budget_id = budget_line[0].id
                if budget_lines:
                    remain = abs(budget_lines.remain)
                    amount = amount + rec.line_total
                    new_balance = remain - amount
                    confirmation_lines.append((0, 0, {
                        'amount': rec.line_total,
                        'analytic_account_id': analytic_account.id,
                        'description': rec.product_id.name,
                        'budget_line_id': budget_lines.id,
                        'remain': remain,
                        'new_balance': new_balance,
                        'account_id': rec.product_id.property_account_expense_id.id and rec.product_id.property_account_expense_id.id or rec.product_id.categ_id.property_account_expense_categ_id.id
                    }))

        data = {
            'name': self.name,
            'date': self.date,
            'beneficiary_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'type': 'purchase.request',
            'ref': self.name,
            'description': self.name,
            'total_amount': total_amount,
            'lines_ids': confirmation_lines or False,
            'request_id': self.id
        }
        self.env['budget.confirmation'].create(data)

    def create_purchase_order2(self):
        if not self.partner_id:
            raise UserError(_("You must set a Vendor this PO"))
        if self.use_analytic:
            analytic_account = self.account_analytic_id.id
        else:
            analytic_account = self.department_id.analytic_account_id.id
        line_ids = []
        for line in self.line_ids:
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'product_qty': line.qty,
                'name': line.description or line.product_id.name,
                'department_name': self.employee_id.department_id.id,
                'account_analytic_id': analytic_account,
                'date_planned': datetime.today(),
                'price_unit': 0,
            }))

        purchase_order = self.env['purchase.order'].sudo().create({
            'category_ids': self.product_category_ids.ids,
            'origin': self.name,
            'request_id': self.id,
            'partner_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'purpose': self.purchase_purpose,
            'purchase_cost': 'product_line',
            'order_line': line_ids,

        })
        self.write({'purchase_create': True})

        return {
            'name': "Purchase orders from employee",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id}


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'
    expected_price = fields.Float(string='Expected Price', tracking=True, )
    line_total = fields.Float(string='Total', compute='_compute_line_total', store=True)

    @api.depends('qty', 'expected_price')
    def _compute_line_total(self) -> None:
        for line in self:
            line.line_total = line.qty * line.expected_price
