# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, Warning, UserError
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            payment = self.env['account.payment'].search([('move_id', '=', rec.id),
                                                          ('payment_type', '=', 'outbound')], limit=1)
            if payment and payment.state != 'posted':
                raise ValidationError(_("You can't post this journal entry because the payment is not posted yet."))
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('depart_manager', 'Department Manager'),
        ('accounting_manager', 'Accounting Manager'),
        ('general_manager', 'General Manager'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', required=True, readonly=True, copy=False, tracking=True)
    state_a = fields.Selection(related='state', tracking=False)
    state_b = fields.Selection(related='state', tracking=False)

    state_history = fields.Char(string='State History', default='draft')
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account', copy=True)
    payments_methods = fields.Selection(selection=[
        ('all', 'تنازلي على الفواتير'),
        ('help', 'شاشة مساعدة على الفواتير'),
        ('down_payment', 'دفعة مقدمة'),
    ], string='طرق السداد')

    invoices_ids = fields.Many2many(
        'account.move',
        'account_payment_invoice_rel',
        'payment_id',
        'invoice_id',
        string='Partner Invoices',
        domain="[('partner_id', '=', partner_id), ('move_type', 'in', ('out_invoice','in_invoice')), ('state','=','posted'), ('payment_state','!=','paid')]"
    )
    pay_invoice = fields.Boolean(string="Payment Invoices")
    invoice_line_ids = fields.One2many(
        'account.payment.invoice.line',
        'payment_id',
        string='Invoice Lines',
        store=True,

    )
    payment_type_selection = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ],default='automatic')

    @api.onchange('invoices_ids')
    def _onchange_invoices_ids(self):
        for rec in self:
            rec.invoice_line_ids = [(5, 0, 0)]

            lines = []
            for invoice in rec.invoices_ids:
                lines.append((0, 0, {
                    'invoice_id': invoice.id,
                    'name': invoice.name,
                }))

            rec.invoice_line_ids = lines

    @api.onchange('payments_methods')
    def _onchange_payments_methods(self):
        if self.payments_methods == 'all':
            self.pay_invoice = True
            self.invoices_ids = False
        elif self.payments_methods == 'help':
            self.pay_invoice = False
        else:
            self.pay_invoice = False
            self.invoices_ids = False



    @api.model
    def create(self, vals):
        vals['state_history'] = 'draft'
        res = super(AccountPayment, self).create(vals)
        if res.analytic_account_id and res.move_id:
            for line in res.move_id.line_ids:
                if line.account_id.id == res.destination_account_id.id:
                    line.analytic_account_id = res.analytic_account_id.id
        return res

    def _check_permission(self, group_xml_id):
        if not self.env.user.has_group(group_xml_id):
            group_name = self.env.ref(group_xml_id).name
            raise AccessError(_("You do not have the necessary permissions (%s) to perform this action.") % group_name)

    def action_post(self):
        if self.payment_type == 'outbound':
            self._check_permission('odex25_account_payment_fix.group_posted')

        res = super(AccountPayment, self).action_post()

        for payment in self:
            payment.state = 'posted'

            # -----------------------------
            # 1) analytic account
            # -----------------------------
            if payment.analytic_account_id and payment.move_id:
                target_lines = payment.move_id.line_ids.filtered(
                    lambda line: line.account_id.id == payment.destination_account_id.id
                )
                target_lines.write({'analytic_account_id': payment.analytic_account_id.id})

            # -----------------------------
            # 2) only inbound payments
            # -----------------------------
            if payment.payment_type != 'inbound':
                continue

            remaining = payment.amount

            # -----------------------------
            # 3) get invoices
            # -----------------------------
            if payment.pay_invoice:
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', payment.partner_id.id),
                    ('move_type', 'in', ('out_invoice', 'in_invoice')),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid'),
                ], order='invoice_date asc')
            else:
                invoices = payment.invoices_ids

            if not invoices:
                continue

            # -----------------------------
            # 4) loop invoices oldest → latest
            # -----------------------------
            for inv in invoices:

                if remaining <= 0:
                    break

                # -----------------------------
                # Load widget safely
                # -----------------------------
                widget = inv.invoice_outstanding_credits_debits_widget

                if not widget:
                    continue

                # Convert JSON string → dict
                if isinstance(widget, str):
                    widget = json.loads(widget)

                if 'content' not in widget:
                    continue

                # find payment line inside widget
                line_to_assign = None
                for line in widget['content']:
                    if line.get('move_id') == payment.move_id.id:
                        line_to_assign = line
                        break

                if not line_to_assign:
                    continue

                residual = inv.amount_residual

                # -----------------------------
                # 5) Error if payment > invoice
                # -----------------------------
                if remaining > residual:
                    # allowed → Odoo will reconcile and remainder goes to next invoice
                    pass
                elif remaining < residual:
                    # allowed → partial reconcile
                    pass
                else:
                    pass

                # Do actual reconcile
                inv.js_assign_outstanding_line(line_to_assign['id'])

                # deduct remaining
                if remaining >= residual:
                    remaining -= residual
                else:
                    remaining = 0
                    break

            # -----------------------------
            # 6) إذا لسه باقي جزء من المبلغ
            # يعني الدفع أكبر من كل الفواتير
            # -----------------------------
            if remaining > 0:
                raise UserError(
                    "❌ المبلغ المدفوع أكبر من قيمة الفواتير.\n"
                    f"المبلغ المتبقي بعد الدفع: {remaining}"
                )

        return res


    def action_cancel(self):
        payment_state = self.state
        res = super(AccountPayment, self).action_cancel()
        for payment in self:
            if self.payment_type == 'outbound' and payment.state != 'draft':
                self._check_permission(f'odex25_account_payment_fix.group_{payment.state}')
                if payment_state == 'draft':
                    payment.state = 'cancel'
                else:
                    payment.state = self.state_history
                    payment.state_history = 'cancel'
            else:
                payment.state = 'cancel'
            if payment.analytic_account_id and payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id.id == payment.destination_account_id.id:
                        line.analytic_account_id = payment.analytic_account_id.id
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for payment in self:
            payment.state = 'draft'
            if payment.analytic_account_id and payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id.id == payment.destination_account_id.id:
                        line.analytic_account_id = payment.analytic_account_id.id
            payment.state_history = 'cancel'
        return res

    def action_depart_manager(self):
        self._check_permission('odex25_account_payment_fix.group_depart_manager')
        self.state_history = self.state
        self.state = 'depart_manager'

    def action_accounting_manager(self):
        self._check_permission('odex25_account_payment_fix.group_accounting_manager')
        self.state_history = self.state
        self.state = 'accounting_manager'

    def action_general_manager(self):
        self._check_permission('odex25_account_payment_fix.group_general_manager')
        self.state_history = self.state
        self.state = 'general_manager'

    def action_multi_depart_manager(self):
        if any(rec.payment_type == 'outbound' and rec.state != 'draft' for rec in self):
            raise ValidationError(_("Action skipped: one or more selected outbound payments are not in the 'Draft' state."))

        for rec in self.filtered(lambda r: r.payment_type == 'outbound' and r.state == 'draft'):
            rec.action_depart_manager()

    def action_multi_accounting_manager(self):
        if any(rec.payment_type == 'outbound' and rec.state != 'depart_manager' for rec in self):
            raise ValidationError(
                _("Action skipped: one or more selected outbound payments are not in the 'Depart Manager' state."))

        for rec in self.filtered(lambda r: r.payment_type == 'outbound' and r.state == 'depart_manager'):
            rec.action_accounting_manager()

    def action_multi_general_manager(self):
        if any(rec.payment_type == 'outbound' and rec.state != 'accounting_manager' for rec in self):
            raise ValidationError(
                _("Action skipped: one or more selected outbound payments are not in the 'Accounting Manager' state."))

        for rec in self.filtered(lambda r: r.payment_type == 'outbound' and r.state == 'accounting_manager'):
            rec.action_general_manager()

    def action_multi_post_payments(self):
        if any(rec.payment_type == 'outbound' and rec.state != 'general_manager' for rec in self):
            raise ValidationError(
                _("Action skipped: one or more selected outbound payments are not in the 'General Manager' state."))

        for rec in self.filtered(lambda r: r.payment_type == 'outbound' and r.state == 'general_manager'):
            rec.action_post()
