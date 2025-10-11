# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
import ast
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


# class HrEmployee(models.Model):
#     _inherit='hr.employee'
#     @api.model
#     def action_open_bank_balance_in_gl(self):
#
#         self.ensure_one()
#         action = self.env["ir.actions.actions"]._for_xml_id("odex25_account_reports.action_account_report_general_ledger")
#         employee = self.browse(self._context.get('active_id'))
#         action['context'] = dict(ast.literal_eval(action['context']), default_filter_accounts=employee.journal_id.default_account_id.code)
#
#         return action


class BaseDashboardExtended(models.Model):
    _inherit = 'base.dashbord'  # Inherit existing dashboard

    # One2many reverse of the Many2one in pledges
    pledge_ids = fields.One2many(
        'hr.request.pledge',
        'dashboard_id',
    
    )

class HrRequestPledge(models.Model):
    _name = 'hr.request.pledge'
    _description = 'Request Pledge'
    _rec_name = "code"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char()
    state = fields.Selection(
        [('draft', _('Draft')),
         ('submit', _('Waiting Payroll Officer')),
         ('direct_manager', _('Wait HR Department')),
         ('hr_manager', _('Wait GM Approval')),
           
         ('executive_manager', _('Wait Transfer')),
         ('financial_approve', _('Wait Financial Approval')),
         ('pay', _('Transferred')), ('refused', _('Refused')),
         ('closed', _('Loan Suspended'))],
        default="draft", tracking=True)
    date = fields.Date(required=True)
    department_id = fields.Many2one(related='employee_id.department_id', readonly=True, store=True)
    from_hr_depart = fields.Boolean()
    job_id = fields.Many2one(related='employee_id.job_id', readonly=True)
    dashboard_id = fields.Many2one(
        'base.dashbord',
        
        index=True
    )
    is_financial_impact = fields.Boolean(
    compute='_compute_is_financial_impact',
    store=True
    )
    custody_type_id = fields.Many2one(
        'custody.types',
        string='Custody Types',
        required=True,
        tracking=True
    )
    journal_id = fields.Many2one(related='custody_type_id.journal_id', readonly=True)


    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  default=lambda item: item.get_user_id(), index=True)

    emp_expect_amount = fields.Float(string='Request Employee Amount')
    description = fields.Char("Statement")


    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    spent_amount = fields.Float(string="Amount Spent", default=0.0)
    remaining_amount = fields.Float(string="Amount Remaining", compute="_compute_remaining_amount", store=True)
    custody_status = fields.Selection([
        ('new', 'New'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('exceeded', 'Exceeded')
    ], string='Custody Status', default='new', tracking=True)

    @api.depends('spent_amount', 'emp_expect_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = (rec.emp_expect_amount or 0.0) - (rec.spent_amount or 0.0)







    @api.model
    def allocate_payment_to_pledges(self, employee_id, journal_id, amount):
        """
        Allocate a payment amount to employee's custody requests ordered by oldest.
        Handles partial, full, and exceeded states.
        """
        remaining_amount = amount

        pledges = self.search([
            ('employee_id', '=', employee_id),
            ('journal_id', '=', journal_id),
            ('custody_status', 'in', ['partial','new' ]),
        ], order="id asc")

        for pledge in pledges:
            if remaining_amount <= 0:
                break

            spent = pledge.spent_amount or 0.0
            total = pledge.emp_expect_amount or 0.0
            pledge_remaining = total - spent

            if pledge_remaining <= 0:
                continue

            allocated = min(pledge_remaining, remaining_amount)
            pledge.spent_amount = spent + allocated

            if pledge.spent_amount < total:
                pledge.custody_status = 'partial'
            elif pledge.spent_amount == total:
                pledge.custody_status = 'paid'

            remaining_amount -= allocated

        if remaining_amount > 0:
            target_pledge = (pledges.filtered(lambda p: p.custody_status == 'partial') or pledges)[-1:]
            for pledge in target_pledge:
                pledge.spent_amount += remaining_amount
                pledge.custody_status = 'exceeded'
                break







    @api.constrains('custody_type_id', 'emp_expect_amount')
    def _check_custody_amount_limit(self):
        for record in self:
            if record.custody_type_id and record.emp_expect_amount:
                if record.emp_expect_amount > record.custody_type_id.max_custody_amount:
                    raise ValidationError(_(
                        "The requested amount (%s) exceeds the maximum allowed for the selected custody type (%s)."
                    ) % (record.emp_expect_amount, record.custody_type_id.max_custody_amount))

    @api.depends('dashboard_id.is_financial_impact')
    def _compute_is_financial_impact(self):
      for record in self:
        
         record.is_financial_impact = record.dashboard_id.is_financial_impact

    

        
    def get_user_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            return employee_id.id
        else:
            return False
        


    # @api.model
    # def default_get(self, fields):
    #   res = super().default_get(fields)
    #   res['journal_id'] = False
    #   return res
    
    
    @api.constrains('emp_expect_amount')
    def _check_positive_emp_expect_amount(self):
        for rec in self:
            if rec.emp_expect_amount <= 0:
                raise ValidationError(
                    _("Employee expect amount should be bigger than zero!")
                )

    @api.model
    def create(self, values):
    
    # Auto-link dashboard if not provided
      if not values.get('dashboard_id'):
        dashboard = self.env['base.dashbord'].search([  # Fix typo: 'base.dashboard'
            ('model_name', '=', self._name)
        ], limit=1)
        if dashboard:
            values['dashboard_id'] = dashboard.id
    
    # Generate sequence code (your existing logic)
      seq = self.env['ir.sequence'].next_by_code('hr.request.pledge') or '/'
      values['code'] = seq  # Assign the sequence to the 'code' field
    
    # Create the record
      return super(HrRequestPledge, self).create(values)

    def submit(self):
        self.state = "submit"

    def direct_manager(self):
        self.state = "direct_manager"

    def hr_manager(self):
        self.state = "hr_manager"

    def executive_manager(self):
        self.state = "executive_manager"

    def refused(self):
        self.state = "refused"

    def cancel(self):
        self.state = "cancel"

    def pay(self):
        if not self.journal_id:
            raise ValidationError(_('Please set the journal for this employee.'))

        employee_partner = self.employee_id.user_id.partner_id
        if not employee_partner:
            raise ValidationError(_('Employee must have a related partner.'))

        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'supplier',
            'is_internal_transfer': True,
            'amount': self.emp_expect_amount,
            'journal_id': self.journal_id.id,
            'date': fields.datetime.today(),
            'ref': self.description,
            'hr_request_pledge': self.id,
        }

        payment = self.env['account.payment'].create(payment_vals)
        payment.flush()
        payment.refresh()

        employee_partner = self.employee_id.user_id.partner_id
        if employee_partner:
            for line in payment.move_id.line_ids:
                if line.debit > 0:
                    line.partner_id = employee_partner.id
                    break

        self.state = "pay"
        return payment

    def financialApproval(self):
        self.state="financial_approve"

    def action_account_payment_budget_pledge(self):
        budget_account_payment = self.env['account.payment'].search(
            [('hr_request_pledge', '=', self.id)],
            limit=1
        )
        if budget_account_payment:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Achieving Budget',
                'res_model': 'account.payment',
                'res_id': budget_account_payment.id,
                'view_mode': 'form',
                'target': 'current',
            }


class SmartButtonReturnRequestPledge(models.Model):
    _inherit = "account.payment"
    hr_request_pledge = fields.Many2one('hr.request.pledge')

    def action_go_to_hr_request_pledge(self):
        pledge_record = self.env['hr.request.pledge'].search(
            [('id', '=', self.hr_request_pledge.id)],
            limit=1
        )
        if pledge_record:
            return {
                'type': 'ir.actions.act_window',
                'name': 'HR Request Pledge',
                'res_model': 'hr.request.pledge',
                'res_id': pledge_record.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }


class EmployeeJournal(models.Model):
    _inherit = "hr.employee"

    journal_id = fields.Many2one('account.journal', domain="[('type', '=', 'cash')]")
    department = fields.Many2one('hr.department', string="Department")
    department_name = fields.Char(
         string='Department Name', 
         related='department.name',
         readonly=True, 
        store=True,
    ) 





    # def action_sheet_move_create(self):
    #     for sheet in self:
    #         if sheet.payment_mode == 'company_account' and not (sheet.bank_journal_id and sheet.account_payment_method_id):
    #             raise UserError(
    #                 _("Please enter Bank Journal and Payment Method!")
    #             )
    #
    #     return super(HrExpenseSheetPledge, self).action_sheet_move_create()


# class AchievingBudgetAchievingBudget(models.Model):
#     _inherit = "hr.expense"

    # action_budget_id = fields.Many2one('account.tax', 'analytic')

    # def _create_sheet_from_expenses(self):
    #     if any(expense.state != 'draft' or expense.sheet_id for expense in self):
    #         raise UserError(_("You cannot report twice the same line!"))
    #     if len(self.mapped('employee_id')) != 1:
    #         raise UserError(_("You cannot report expenses for different employees in the same report."))
    #     if any(not expense.product_id for expense in self):
    #         raise UserError(_("You can not create report without product."))
    #     if len(self.company_id) != 1:
    #         raise UserError(_("You cannot report expenses for different companies in the same report."))

    #     todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
    #     sheet = self.env['hr.expense.sheet'].create({
    #         'company_id': self.company_id.id,
    #         'employee_id': self[0].employee_id.id,
    #         'name': todo[0].name if len(todo) == 1 else '',
    #         'expense_line_ids': [(6, 0, todo.ids)],
    #     })
    #     # sheet.write({
    #     #     'account_payment_method_id': sheet.bank_journal_id.outbound_payment_method_line_ids[:1]
    #     # })
    #     return sheet

    # def action_achieving_budget_pledge(self):
    #     achieving_budget_record = self.env['budget.confirmation'].search(
    #         [('expense_id', '=', self.id)],
    #         limit=1
    #     )
    #     if achieving_budget_record:
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Achieving Budget',
    #             'res_model': 'budget.confirmation',
    #             'res_id': achieving_budget_record.id,
    #             'view_mode': 'form',
    #             'target': 'current',
    #         }


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _employee_custody_lines_view(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        if not employee:
            raise UserError("There is no employee associated with this user.")

        account_id = employee.journal_id.default_account_id.id

        if not account_id:
            raise UserError("The employee does not have an associated journal or default account.")

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Employee Account Report',
            'res_model': 'account.move.line',
            'view_mode': 'tree',
            'view_id': self.env.ref('employee_custody_request.view_account_move_line_tree_custom').id,
            'domain': [('account_id', '=', account_id)],
            'context': {
            },
            'target': 'current',
        }
        return action
