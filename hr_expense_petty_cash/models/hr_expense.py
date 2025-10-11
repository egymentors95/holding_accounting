from odoo import _, fields, models, api
from odoo.exceptions import UserError

from odoo.tools import float_round
from collections import defaultdict
class HrExpense(models.Model):
    _inherit = "hr.expense"
    # user_partner_id
    partner_id = fields.Many2one(
        'res.partner', string='Vendor', readonly=True,
        states={"draft": [("readonly", False)]}
    )
    address_id = fields.Many2one(
        'res.partner', related='employee_id.user_id.partner_id'
    )
    vat = fields.Char(
        related='partner_id.vat', string='TIN', readonly=False
    )
    payment_mode = fields.Selection(
        selection_add=[("petty_cash", "Petty Cash")]
    )
    petty_cash_id = fields.Many2one(
        string="Petty cash holder",
        comodel_name="petty.cash",
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    # override compute amount_res

    petty_cash_limit = fields.Float(string="Amount", related='petty_cash_id.petty_cash_limit',  readonly=True,)
    @api.depends("sheet_id.account_move_id.line_ids",'petty_cash_limit','total_amount','petty_cash_id')
    def _compute_amount_residual(self):
        for expense in self:
            # if not expense.sheet_id:
            #     expense.amount_residual = expense.total_amount
            #     continue
            # if  expense.petty_cash_limit>0:

            if not expense.currency_id or expense.currency_id == expense.company_id.currency_id:
                residual_field = 'amount_residual'
            else:
                residual_field = 'amount_residual_currency'
            payment_term_lines = expense.sheet_id.account_move_id.line_ids \
                .filtered(lambda line: line.expense_id == expense and line.account_internal_type in ('receivable', 'payable'))
            expense.amount_residual = -sum(payment_term_lines.mapped(residual_field))
            expense.amount_residual = expense.petty_cash_limit-expense.total_amount


    @api.constrains("petty_cash_id", "total_amount")
    def _check_expense_limit(self):
        amount_to_check = (self.petty_cash_id.percent_to_reconcile / 100) * self.petty_cash_id.petty_cash_limit
        if 0 < self.petty_cash_id.expense_limit < self.total_amount:
            raise UserError(_('Expenses amount can not exceed the expense limit %s') % self.petty_cash_id.expense_limit)
        elif amount_to_check and self.petty_cash_id.petty_cash_expenses + self.total_amount > amount_to_check:
            raise UserError(
                _('Expenses amount can not exceed the limit percent %s') % amount_to_check)

    def _prepare_expense_vals(self):
        vals = {
            "company_id": self.company_id.id,
            "employee_id": self[0].employee_id.id,
            "name": self[0].name if len(self) == 1 else "",
            "expense_line_ids": [(6, 0, self.ids)],
        }
        return vals

    def _create_sheet_from_expense_petty_cash(self):
        """ Overwrite function _create_sheet_from_expenses(), if petty cash mode. """
        if any(expense.state != "draft" or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped("employee_id")) != 1:
            raise UserError(
                _(
                    "You cannot report expenses for different "
                    "employees in the same report."
                )
            )
        if any(not expense.product_id for expense in self):
            raise UserError(_("You can not create report without product."))
        ctx = self._context.copy()
        ctx.update({"default_petty_cash_id": self[0].petty_cash_id.id})
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
        return super()._create_sheet_from_expenses()

    def _get_account_move_line_values(self):
        res = super()._get_account_move_line_values()
        for expense in self.filtered(lambda p: p.payment_mode == "petty_cash"):
            line = res[expense.id][len(res[expense.id]) - 1]
            line["account_id"] = expense.petty_cash_id.account_id.id
            line["partner_id"] = expense.petty_cash_id.partner_id.id
            line["petty_cash_id"] = expense.petty_cash_id.id
            res[expense.id][len(res[expense.id]) - 1] = line
        return res

    def refuse_expense(self, reason):
        self.write({'is_refused': True, 'state': 'refused'})
        self.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                    values={'reason': reason, 'is_sheet': False, 'name': self.name})
        self.sheet_id.message_post_with_view('hr_expense.hr_expense_template_refuse_reason',
                                             values={'reason': reason, 'is_sheet': False, 'name': self.name})

    def action_move_create(self):
        # Filter out refused expenses
        expenses = self.filtered(lambda x: not x.is_refused)
        
        return super(HrExpense, expenses).action_move_create()
