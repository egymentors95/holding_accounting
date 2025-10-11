from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, pycompat


class BudgetConfirmationCustom(models.Model):
    _inherit = 'budget.confirmation'

    type = fields.Selection(selection_add=[('vendor.bill', 'Vendor Bill')])
    invoice_id = fields.Many2one('account.move')

    def cancel(self):
        super(BudgetConfirmationCustom, self).cancel()
        if self.invoice_id and self.type == 'vendor.bill':
            self.invoice_id.write({'state': 'draft'})
            self.invoice_id.message_post(body=_(
                "Rejected By : %s  With Reject Reason : %s" % (str(self.env.user.name), str(self.reject_reason or self.env.context.get('reject_reason','')))))


    def done(self):
        super(BudgetConfirmationCustom, self).done()
        if self.invoice_id and self.type == 'vendor.bill':
            self.invoice_id.write({'is_approve': True})
            self.invoice_id.write({'state': 'budget_approve'})
            for rec in self:
                for line in rec.lines_ids:
                    budget_post = self.env['account.budget.post'].search([]).filtered(
                        lambda x: line.account_id in x.account_ids)
                    analytic_account_id = line.analytic_account_id
                    budget_lines = analytic_account_id.crossovered_budget_line.filtered(
                        lambda x: x.general_budget_id in budget_post and
                                  x.crossovered_budget_id.state == 'done' and
                                  x.date_from <= self.date <= x.date_to)
                    if len(budget_lines) > 1:
                        budget_lines = budget_lines[0]
                    print("budget_lines.reserve budget_lines.reserve budget_lines.reserve", budget_lines.reserve)
                    amount = budget_lines.reserve
                    amount += line.amount
                    budget_lines.write({'reserve': amount})


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('wait_budget', 'Wait Budget'),
        ('budget_approve', 'Approved'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ])

    state_a = fields.Selection(related='state')
    state_b = fields.Selection(related='state')

    is_budget = fields.Boolean(defaul=True)
    state_bill = fields.Selection(related='state')
    budget_check = fields.Boolean(string="Check Budget", default=False, readonly=True)
    exceed_budget = fields.Boolean(defaul=False)
    is_check = fields.Boolean(defaul=False)
    is_approve = fields.Boolean(defaul=False)
    hide_budget = fields.Boolean(defaul=False,copy=False)
    rec_payment_count = fields.Integer(compute='_compute_rec_payment_count', string='# Payments')

    def _compute_rec_payment_count(self):
        # for invoice in self:
        #     payments = self.env['account.payment'].sudo().search_count([
        #         ('invoice_rec_id', '=', invoice.id)
        #     ])
        #     invoice.rec_payment_count = payments
        for invoice in self:
            payments = self.env['account.payment'].sudo().search([]).filtered(lambda r: invoice.id in r.invoice_rec_ids.ids)
            invoice.rec_payment_count = len(payments)

    def action_open_related_payment_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        # payments = self.env['account.payment'].search([
        #     ('invoice_rec_id', '=', self.id)
        # ]).ids
        payments = self.env['account.payment'].search([]).filtered(lambda r: self.id in r.invoice_rec_ids.ids).ids

        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payments)],
        }
    def copy(self):
        self.write({'budget_check': False})
        # self.write({'is_check':False})
        return super(AccountMove, self).copy()

    def action_confirm(self):
        if not self.invoice_date:
            raise ValidationError(_('Please insert Bill Date'))
        for rec in self.invoice_line_ids:
            if rec.analytic_account_id.is_analytic_budget and not rec.analytic_account_id.is_auto_check:
                self.write({
                    'state': 'confirm',
                    'hide_budget': False
                })
                break
            else:
                self.write({
                    'state': 'budget_approve'
                })
        if self.purchase_id:
            confirm_budget = self.env['budget.confirmation'].search([('po_id', '=', self.purchase_id.id)], limit=1,
                                                                    order='id desc')
            if confirm_budget:
                confirm_budget.invoice_id = self.id
                self.write({
                    'is_check': True,
                    'state': 'budget_approve' if confirm_budget.state == 'done' else 'wait_budget'
                })
                return True

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.is_check:
            date = fields.Date.from_string(self.date)
            for line in self.invoice_line_ids:
                analytic_account_id = line.analytic_account_id
                budget_post = self.env['account.budget.post'].search([]).filtered(
                    lambda x: line.account_id in x.account_ids)
                budget_lines = analytic_account_id.crossovered_budget_line.filtered(
                    lambda x: x.general_budget_id in budget_post and
                              x.crossovered_budget_id.state == 'done' and
                              fields.Date.from_string(x.date_from) <= date <= fields.Date.from_string(x.date_to))
                amount = budget_lines.reserve
                amount -= (line.price_subtotal + line.price_tax)
                budget_lines.write({'reserve': amount})

        return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.is_check:
            confirm_budget = self.env['budget.confirmation'].search([('invoice_id', '=', self.id)])
            confirm_budget.write({'ref': self.name})
            for line in self.invoice_line_ids:
                analytic_account_id = line.analytic_account_id
                budget_post = self.env['account.budget.post'].search([]).filtered(
                    lambda x: line.account_id in x.account_ids)
                budget_lines = analytic_account_id.crossovered_budget_line.filtered(
                    lambda x: x.general_budget_id in budget_post and
                              x.crossovered_budget_id.state == 'done' and
                              x.date_from <= self.invoice_date <= x.date_to)
                amount = budget_lines.confirm
                amount += (line.price_subtotal + line.price_tax)
                budget_lines.write({'confirm': amount})
                budget_lines.write({'reserve': abs((line.price_subtotal + line.price_tax) - budget_lines.reserve)})
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for rec in self:
            if rec.is_check:
                date = fields.Date.from_string(rec.date)
                for line in rec.invoice_line_ids:
                    analytic_account_id = line.analytic_account_id
                    budget_post = self.env['account.budget.post'].search([]).filtered(
                        lambda x: line.account_id in x.account_ids)
                    budget_lines = analytic_account_id.crossovered_budget_line.filtered(
                        lambda x: x.general_budget_id in budget_post and
                                  x.crossovered_budget_id.state == 'done' and
                                  fields.Date.from_string(x.date_from) <= date <= fields.Date.from_string(x.date_to))
                    amount = budget_lines.confirm
                    amount -= (line.price_subtotal + line.price_tax)
                    budget_lines.write({'confirm': amount})
        return res

    def action_budget(self):
        confirmation_lines = []
        self.hide_budget = True
        if not self.budget_check:
            amount = 0
            if self.purchase_id:
                confirm_budget = self.env['budget.confirmation'].search([('po_id', '=', self.purchase_id.id)], limit=1,
                                                                        order='id desc')
                if confirm_budget:
                    confirm_budget.invoice_id = self.id
                    self.write({
                        'is_check': True,
                        'state': 'budget_approve' if confirm_budget.state == 'done' else 'wait_budget'
                    })
                    if confirm_budget.state =='cancel':
                        confirm_budget.state='draft'
                    return True
            for line in self.invoice_line_ids.filtered(lambda r: r.analytic_account_id.is_analytic_budget == True):
                if line.analytic_account_id:
                    if not line.analytic_account_id:
                        raise ValidationError(_('Please Choose Analytic account for This Bill'))
                    budget_post = self.env['account.budget.post'].search([]).filtered(lambda x: line.account_id in x.account_ids)
                    if len(budget_post.ids) > 1:
                        raise ValidationError(
                            _("The Expense account %s is assigned to more than one budget position %s")%(line.account_id.name,[x.name for x in budget_post]))
                    budget_lines = self.env['crossovered.budget.lines'].search(
                        [('analytic_account_id', '=', line.analytic_account_id.id),
                         ('general_budget_id', 'in', budget_post.ids),
                         ('crossovered_budget_id.state', '=', 'done'),
                         ('crossovered_budget_id.date_from', '<=', self.invoice_date),
                         ('crossovered_budget_id.date_to', '>=', self.invoice_date)])
                    if not budget_lines:
                        confirmation_lines=[]
                    else:
                        remain = abs(budget_lines.remain)
                        tax_id = line.tax_ids[0].analytic if line.tax_ids else False
                        amount = amount + (line.price_subtotal +  (line.price_tax if tax_id else 0))
                        new_remain = remain - amount
                        confirmation_lines.append((0, 0, {
                            'amount': line.price_subtotal + (line.price_tax if tax_id else 0),
                            'analytic_account_id': line.analytic_account_id.id,
                            'description': line.product_id.name,
                            'budget_line_id': budget_lines.id,
                            'remain': new_remain + (line.price_subtotal + line.price_tax),
                            'new_balance': new_remain,
                            'account_id': line.account_id.id
                        }))

            data = {
                'name': _('Vendor Bill :%s') % self.partner_id.name,
                'date': self.invoice_date,
                'beneficiary_id': self.partner_id.id,
                'type': 'vendor.bill',
                'ref': self.name,
                'description': self.ref,
                'total_amount': amount,
                'lines_ids': confirmation_lines,
                'invoice_id': self.id
            }
            self.env['budget.confirmation'].create(data)
            self.write({
                'state': 'wait_budget'
            })
    def open_confirmation(self):
        formview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_form', False)
        treeview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_tree', False)
        confirm_budget = self.env['budget.confirmation'].search([('invoice_id', '=', self.id)])
        return {
            'name': ("Budget  Confirmation"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'budget.confirmation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % confirm_budget.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {'create': False}
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'account.move.line'

    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            taxes = line.tax_ids.compute_all(line.price_unit, line.move_id.currency_id, line.quantity,
                                             product=line.product_id, partner=line.move_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
            })
