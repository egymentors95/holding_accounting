from odoo import api, fields, models, tools, _
import ast
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payment_mode = fields.Selection(
        selection_add=[
            ("custody", "Custody")
        ]
    )

    def _create_sheet_from_expense_custody(self):
        """Create expense sheet for custody mode"""
        if any(expense.state != "draft" or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped("employee_id")) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))
        if any(not expense.product_id for expense in self):
            raise UserError(_("You cannot create a report without product."))

        ctx = self._context.copy()
        sheet = (
            self.env["hr.expense.sheet"]
            .with_context(ctx)
            .create(self._prepare_expense_vals())
        )
        sheet._compute_from_employee_id()
        return sheet

    def _create_sheet_from_expenses(self):
        payment_mode = set(self.mapped("payment_mode"))
        if len(payment_mode) > 1 and "petty_cash" in payment_mode:
            raise UserError(
                _("You cannot create report from many petty cash mode and other.")
            )
        if all(expense.payment_mode == "petty_cash" for expense in self):
            return self._create_sheet_from_expense_petty_cash()
        if all(expense.payment_mode == "custody" for expense in self):
            return self._create_sheet_from_expense_custody()
        return super()._create_sheet_from_expenses()

    def _get_expense_account_destination(self):
        self.ensure_one()

        if self.payment_mode == 'company_account':
            if self.sheet_id.account_payment_method_id:
                account_dest = self.sheet_id.account_payment_method_id.payment_account_id.id
            else:
                if not self.sheet_id.bank_journal_id.payment_credit_account_id:
                    raise UserError(
                        _("No Outstanding Payments Account found for the %s journal, please configure one.") % (
                            self.sheet_id.bank_journal_id.name))
                account_dest = self.sheet_id.bank_journal_id.payment_credit_account_id.id

        elif self.payment_mode == 'custody':
            if self.sheet_id.account_payment_method_id:
                account_dest = self.sheet_id.account_payment_method_id.payment_account_id.id
            else:
                if not self.sheet_id.custody_bank_journal_id.payment_credit_account_id:
                    raise UserError(
                        _("No Outstanding Payments Account found for the %s journal, please configure one.") % (
                            self.sheet_id.custody_bank_journal_id.name))
                account_dest = self.sheet_id.custody_bank_journal_id.payment_credit_account_id.id

        else:
            return super(HrExpense, self)._get_expense_account_destination()

        return account_dest

    def _prepare_move_values(self):
        """Override to handle custody payment mode like company_account"""
        self.ensure_one()

        if self.payment_mode == 'company_account':
            journal = self.sheet_id.bank_journal_id
        elif self.payment_mode == 'custody':
            journal = self.sheet_id.custody_bank_journal_id or self.sheet_id.bank_journal_id
        else:
            journal = self.sheet_id.journal_id

        account_date = self.sheet_id.accounting_date or self.date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.sheet_id.company_id.id,
            'date': account_date,
            'ref': self.sheet_id.name,
            'name': '/',
        }
        return move_values

    def action_move_create(self):
        move_group_by_sheet = super().action_move_create()

        for expense in self:
            if expense.payment_mode == 'custody':
                move = expense.sheet_id.account_move_id
                partner_id = expense.sheet_id.custody_partner_id.id if expense.sheet_id.custody_partner_id else \
                    expense.employee_id.sudo().address_home_id.commercial_partner_id.id
                amount =0
                for line in move.line_ids:
                    if line.credit > 0:
                        amount += line.credit
                        line.write({'partner_id': partner_id})
                if move.state == 'posted':
                    print("amount",amount)
                    employee = self.env['hr.employee'].sudo().search([
                        ('user_id.partner_id', '=', partner_id)
                    ], limit=1)

                    if employee:

                        self.env['hr.request.pledge'].allocate_payment_to_pledges(
                            employee_id=employee.id,
                            journal_id=move.journal_id.id,
                            amount=amount
                        )

                    print(f"✅ posted {move.name} expense {expense.name}")
                else:
                    print(f"❌ not posted {expense.name}")

        return move_group_by_sheet