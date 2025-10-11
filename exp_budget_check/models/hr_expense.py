from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, pycompat


# class BudgetConfirmationCustom(models.Model):
#     _inherit = 'budget.confirmation'

#     type = fields.Selection(selection_add=[('expense', 'Expense')])
#     expense_id = fields.Many2one('hr.expense')

#     def cancel(self):
#         super(BudgetConfirmationCustom, self).cancel()
#         if self.expense_id and self.type == 'expense':
#             self.expense_id.write({'state': 'draft'})
#             self.expense_id.message_post(body=_(
#                 "Rejected By : %s  With Reject Reason : %s" % (str(self.env.user.name), str(self.reject_reason or self.env.context.get('reject_reason','')))))

#     def done(self):
#         super(BudgetConfirmationCustom, self).done()
#         if self.expense_id and self.type == 'expense':
#             self.expense_id.write({'is_approve': True})
#             self.expense_id.write({'state': 'budget_approve'})
#             for rec in self:
#                 for line in rec.lines_ids:
#                     budget_post = self.env['account.budget.post'].search([]).filtered(
#                         lambda x: line.account_id in x.account_ids)
#                     analytic_account_id = line.analytic_account_id
#                     budget_lines = analytic_account_id.crossovered_budget_line.filtered(
#                         lambda x: x.general_budget_id in budget_post and
#                                   x.crossovered_budget_id.state == 'done' and
#                                   x.date_from <= self.date <= x.date_to)
#                     print("budget_lines.reserve budget_lines.reserve budget_lines.reserve", budget_lines.reserve)
#                     amount = budget_lines.reserve
#                     amount += line.amount
#                     budget_lines.write({'reserve': amount})


# class AccountMove(models.Model):
#     _inherit = 'hr.expense'

#     partner_id = fields.Many2one(
#         'res.partner', string='Vendor', readonly=True,
#         states={"draft": [("readonly", False)]}
#     )
#     address_id = fields.Many2one(
#         'res.partner', related='employee_id.user_id.partner_id')
#     state = fields.Selection(selection_add=[
#         ('confirm', 'Confirm'),
#         ('wait_budget', 'Wait Budget'),
#         ('budget_approve', 'Approved'),
#     ])

#     is_budget = fields.Boolean(related='analytic_account_id.is_analytic_budget')
#     is_check = fields.Boolean(defaul=False, copy=False)
#     is_approve = fields.Boolean(defaul=False, copy=False)

#     def action_submit_expenses(self):
#             for record in self:
#                 if record.analytic_account_id.is_analytic_budget:
#                     # if record.state == 'draft':
#                     #     record.write({'state': 'confirm'})
#                     if record.state == 'confirm' and not record.is_approve:
#                         raise UserError(_('Please Check Budget First'))
#                     elif record.state == 'confirm' and record.is_approve:
#                         break
#                     elif record.state == 'wait_budget':
#                         raise UserError(_("The Budget Confirmation Doesn't Approve yet"))
#                     elif record.state == 'budget_approve':
#                         if record.is_approve:
#                             confirm_budget = self.env['budget.confirmation'].search([('expense_id', '=', record.id)])
#                             confirm_budget.write({'ref': record.name})
    
#                             analytic_account_id = record.analytic_account_id
#                             budget_post = self.env['account.budget.post'].search([]).filtered(
#                                 lambda x: record.account_id in x.account_ids)
    
#                             budget_lines = analytic_account_id.crossovered_budget_line.filtered(
#                                 lambda x: x.general_budget_id in budget_post and
#                                           x.crossovered_budget_id.state == 'done' and
#                                           x.date_from <= record.date <= x.date_to)
    
#                             amount = budget_lines.confirm
#                             amount += record.total_amount
#                             budget_lines.write({'confirm': amount})
#                             budget_lines.write({'reserve': abs(record.total_amount - budget_lines.reserve)})
    
#                             todo = record.filtered(lambda x: x.payment_mode == 'own_account') or record.filtered(
#                                 lambda x: x.payment_mode == 'company_account')
    
#                             sheet = self.env['hr.expense.sheet'].create({
#                                 'company_id': record.company_id.id,
#                                 'employee_id': record.employee_id.id,
#                                 'name': todo[0].name if len(todo) == 1 else '',
#                                 'expense_line_ids': [(6, 0, todo.ids)]
#                             })
    
#                             return {
#                                 'name': _('New Expense Report'),
#                                 'type': 'ir.actions.act_window',
#                                 'view_mode': 'form',
#                                 'res_model': 'hr.expense.sheet',
#                                 'target': 'current',
#                                 'res_id': sheet.id,
#                             }
#                 else:
#                     return super(AccountMove, record).action_submit_expenses()
#             return super(AccountMove, self).action_submit_expenses()
#     def button_cancel(self):
#         res = super(AccountMove, self).button_cancel()
#         if self.is_check:
#             date = fields.Date.from_string(self.date)
#             for line in self.invoice_line_ids:
#                 analytic_account_id = line.analytic_account_id
#                 budget_post = self.env['account.budget.post'].search([]).filtered(
#                     lambda x: line.account_id in x.account_ids)
#                 budget_lines = analytic_account_id.crossovered_budget_line.filtered(
#                     lambda x: x.general_budget_id in budget_post and
#                               x.crossovered_budget_id.state == 'done' and
#                               fields.Date.from_string(x.date_from) <= date <= fields.Date.from_string(x.date_to))
#                 amount = budget_lines.reserve
#                 amount -= (line.price_subtotal + line.price_tax)
#                 budget_lines.write({'reserve': amount})

#         return res

#     def button_draft(self):
#         res = super(AccountMove, self).button_draft()
#         if self.is_check:
#             date = fields.Date.from_string(self.date)
#             for line in self.invoice_line_ids:
#                 analytic_account_id = line.analytic_account_id
#                 budget_post = self.env['account.budget.post'].search([]).filtered(
#                     lambda x: line.account_id in x.account_ids)
#                 budget_lines = analytic_account_id.crossovered_budget_line.filtered(
#                     lambda x: x.general_budget_id in budget_post and
#                               x.crossovered_budget_id.state == 'done' and
#                               fields.Date.from_string(x.date_from) <= date <= fields.Date.from_string(x.date_to))
#                 amount = budget_lines.confirm
#                 amount -= (line.price_subtotal + line.price_tax)
#                 budget_lines.write({'confirm': amount})
#         return res

#     def action_budget(self):

#         budget_post = self.env['account.budget.post'].search([]).filtered(lambda x: self.account_id in x.account_ids)
#         if len(budget_post.ids) > 1:
#             raise ValidationError(
#                 _("The Expense account %s is assigned to more than one budget position %s") % (
#                 self.account_id.name, [x.name for x in budget_post]))
#         budget_lines = self.env['crossovered.budget.lines'].search(
#             [('analytic_account_id', '=', self.analytic_account_id.id),
#              ('general_budget_id', 'in', budget_post.ids),
#              ('crossovered_budget_id.state', '=', 'done'),
#              ('crossovered_budget_id.date_from', '<=', self.date),
#              ('crossovered_budget_id.date_to', '>=', self.date)])

#         budget_line = budget_lines
#         if budget_line:
#             remain = abs(budget_line.remain) if budget_line else 0
#             tax_id = self.tax_ids[0].analytic if self.tax_ids else False
#             price_before_tax= self.unit_amount* self.quantity
#             tax_price = self.total_amount - price_before_tax
#             amount = price_before_tax + (tax_price if tax_id else 0)
#             new_remain = remain - amount
#         else:
#             new_remain = 0
#             amount=0
#         data = {
#             'name': _('Expense: %s') % self.employee_id.name,
#             'date': self.date,
#             'beneficiary_id': self.employee_id.user_id.partner_id.id,
#             'type': 'expense',
#             'ref': self.name,
#             'description': self.name,
#             'total_amount': amount,
#             'lines_ids': [(0, 0, {
#                 'amount': amount,
#                 'analytic_account_id': self.analytic_account_id.id,
#                 'description': self.product_id.name,
#                 'budget_line_id': budget_line.id if budget_line else False,
#                 'remain': new_remain + amount,
#                 'new_balance': new_remain,
#                 'account_id': self.account_id.id
#             })] if budget_line else False,
#             'expense_id': self.id
#         }
#         self.env['budget.confirmation'].create(data)

#         self.write({
#             'is_check': True,
#             'state': 'wait_budget'
#         })

#     def action_budget_skip(self):
#         self.write({
#             'is_approve': True,
#             'state': 'confirm'
#         })
#         return True
