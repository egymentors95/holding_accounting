from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
import calendar
from datetime import date
from lxml import etree
import json


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    # todo start
    # make user_id related to manager in employee_id

    parent_id = fields.Many2one('hr.employee', 'Manager',related='employee_id.parent_id', store=True,readonly=True,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
   #     todo end

    @api.model
    def _default_journal_id(self):
        """ Update expense journal from petty cash """
        journal = super()._default_journal_id()
        petty_cash_obj = self.env["petty.cash"]
        petty_cash = self._context.get("default_petty_cash_id", False)
        if petty_cash:
            petty_cash_id = petty_cash_obj.browse(petty_cash)
            journal = petty_cash_id.journal_id.id or journal
        return journal

    petty_cash_id = fields.Many2one(
        string="Petty cash holder",
        comodel_name="petty.cash",
        ondelete="restrict",
        compute="_compute_petty_cash",
        store=True
    )

    journal_id = fields.Many2one(
        default=_default_journal_id
    )
    petty_cash_limit = fields.Float(
        related="petty_cash_id.petty_cash_limit",
        store=True
    )
    petty_cash_balance = fields.Float(
        related="petty_cash_id.petty_cash_balance"
    )
    petty_cash_remaining = fields.Float(
        related="petty_cash_id.petty_cash_remaining"
    )
    
    type = fields.Selection(related="petty_cash_id.type")
    petty_cash_type = fields.Selection(selection=[('renew', 'Replace'), ('close', 'Close')], )
    clearance_type = fields.Selection(
        selection=[('account', 'Accounting'), ('payroll', 'Payroll')], )
    # ('transfer', 'Transfer To Running petty cash')
    # transfer_petty_cash_id = fields.Many2one('petty.cash', string="Transfer To")
    transfer_petty_id = fields.Many2one('petty.cash', string="Transfer To")
    transfer_amount = fields.Float()

    # TODO open this when hr modules is ready
    salary = fields.Boolean()
    salary_rule_id = fields.Many2one('hr.salary.rule', domain=['|', ('category_id.rule_type', '=', 'deduction'),
                                                               ('category_id.name', '=', 'Deduction')])
    payment_amount = fields.Monetary('Payment Amount', currency_field='currency_id', compute='_compute_payment_amount',
                                     store=True)
    transfer_move_id = fields.Many2one('account.move', string="Transfer journal entry")

    # TODO open this when hr modules is ready
    advantage_id = fields.Many2one('contract.advantage')

    # TODO open this when hr modules is ready
    @api.onchange('clearance_type')
    def onchange_clearance_type(self):
        if self.clearance_type != 'payroll':
            self.salary_rule_id = False
    #         todod start
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            print('sheets')
            context = {}
        res = super(HrExpenseSheet, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res['arch'])
        my_group_gid = self.env.ref('hr_expense_petty_cash.group_petty_cash_user').id
        my_group_gid2 = self.env.ref('hr_expense_petty_cash.group_petty_cash_manager').id
        current_user_gids = self.env.user.groups_id.mapped('id')
        default_is_petty_cash = self.env.context.get('default_is_petty_cash')
        # add condition
        if (my_group_gid in current_user_gids and my_group_gid2 not in current_user_gids ):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='approve_expense_sheets']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='reset_expense_sheets']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res
    # todo end
    def action_done(self):
        if self.clearance_type == 'transfer' and self.payment_amount <= 0:
            raise ValidationError(_("There is no remaining Amount to transfer."))
        if self.payment_mode == 'petty_cash' and self.clearance_type == 'transfer':
            journal = self.transfer_petty_id.journal_id
            account_date = self.accounting_date
            if not journal:
                raise ValidationError(
                    _("Kindly insert journal in petty cash %s.") % (self.transfer_petty_id.name))
            first_line = {
                'name': _("Transfer remining Amount to petty cash %s") % (self.transfer_petty_id.name),
                'date_maturity': account_date,
                'debit': self.payment_amount,
                'credit': 0.0,
                'partner_id': self.transfer_petty_id.partner_id.id,
                'account_id': self.transfer_petty_id.account_id.id,
                'petty_cash_id': self.transfer_petty_id.id,
            }
            second_line = {
                'name': _("Transfer remining Amount From petty cash Expenses %s") % (self.name),
                'date_maturity': account_date,
                'debit': 0.0,
                'credit': self.payment_amount,
                'partner_id': self.petty_cash_id.partner_id.id,
                'account_id': self.petty_cash_id.account_id.id,
                'petty_cash_id': self.petty_cash_id.id,
            }
            move_values = {
                'journal_id': journal.id,
                'company_id': self.company_id.id,
                'date': account_date,
                'ref': _("Transfer petty cash remining Amount from %s To %s") % (
                    self.name, self.transfer_petty_id.name),
                'name': '/',
                'line_ids': [(0, 0, first_line), (0, 0, second_line)]
            }
            transfer_move_id = self.env['account.move'].create(move_values)
            transfer_move_id._post()
            self.transfer_move_id = transfer_move_id
            self.transfer_petty_id.petty_cash_limit += self.payment_amount
            # self.transfer_petty_id.transfer_expense_ids += self
            self.petty_cash_id.act_check_balance_to_close()
        self.write({'state': 'done'})

    @api.depends('petty_cash_id', 'petty_cash_id.partner_id', 'petty_cash_id.account_id', 'state')
    def _compute_payment_amount(self):
        for sheet in self:
            petty_cash_move_lines = self.env['account.move.line'].search(
                [('account_id', '=', sheet.petty_cash_id.account_id.id),
                 ('move_id.petty_cash_id', '=', sheet.petty_cash_id.id),
                 ('partner_id', '=', sheet.petty_cash_id.partner_id.id), ('move_id.state', '=', 'posted')])
            company_currency_id = (self.company_id or self.env.company).currency_id
            total_balance = sum(petty_cash_move_lines.mapped(lambda l: company_currency_id.round(l.balance)))
            sheet.payment_amount = total_balance

    @api.model
    def create(self, vals):
        # solve issue in list
        # Check if the list is not empty before accessing its elements
        if "expense_line_ids" in vals.keys() and vals["expense_line_ids"]:
            first_element = vals["expense_line_ids"][0]
            from_expense = first_element[2]
            expenses = self.env["hr.expense"].browse(from_expense)
            exp_petty_cash = all(exp.payment_mode == "petty_cash" for exp in expenses)
            number = self.env["ir.sequence"].next_by_code(
                "hr.expense.sheet.petty.cash"
            )
            vals["name"] = number
        return super().create(vals)

    @api.depends("expense_line_ids", "payment_mode")
    def _compute_petty_cash(self):
        for rec in self:
            rec.petty_cash_id = False
            if rec.payment_mode == "petty_cash" and rec.expense_line_ids:
                set_petty_cash_ids = set()
                for line in rec.expense_line_ids:
                    set_petty_cash_ids.add(line.petty_cash_id.id)
                if len(set_petty_cash_ids) == 1:
                    rec.petty_cash_id = rec.env["petty.cash"].browse(
                        set_petty_cash_ids.pop()
                    )
                else:
                    raise ValidationError(
                        _("You cannot create report from different petty cash.")
                    )

    # TODO : closed because user can enter expensess more tham petty cash amount
    # @api.constrains("expense_line_ids", "total_amount")
    # def _check_petty_cash_amount(self):
    #     for rec in self:
    #         if rec.payment_mode == "petty_cash":
    #             petty_cash = rec.petty_cash_id
    #             balance = petty_cash.petty_cash_balance
    #             amount = rec.total_amount
    #             company_currency = rec.company_id.currency_id
    #             amount_company = rec.currency_id._convert(
    #                 amount,
    #                 company_currency,
    #                 rec.company_id,
    #                 rec.accounting_date or fields.Date.today(),
    #             )
    #             prec = rec.currency_id.rounding
    #             if float_compare(amount_company, balance, precision_rounding=prec) == 1:
    #                 raise ValidationError(
    #                     _(
    #                         "Not enough money in petty cash holder.\n"
    #                         "You are requesting %s%s, "
    #                         "but the balance is %s%s."
    #                     )
    #                     % (
    #                         "{:,.2f}".format(amount_company),
    #                         company_currency.symbol,
    #                         "{:,.2f}".format(balance),
    #                         company_currency.symbol,
    #                     )
    #                 )

    # def action_sheet_move_create(self):
    #     res = super().action_sheet_move_create()
    #     self.expense_line_ids.filtered(lambda x: x.is_refused == True).write({'state': 'refused'})
    #     for key, item in res.items():
    #         sheet = self.browse(key)
    #         item.write({'petty_cash_id': sheet.petty_cash_id.id})
    #     return res

    def action_sheet_move_create(self):
        """
        overwrite the function to write petty_cash_id in created moves 
        and change record state to post when payment mode == petty_cash
        """
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            if samples.count(False):
                raise UserError(_("You can't mix sample expenses and regular ones"))
            self.write({'state': 'post'})
            return

        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(
                r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()
        # for item in res:
        #     for line in item.line_ids:
        #         line.account_id = self.
        # write petty_cash_id in created moves
        self.expense_line_ids.filtered(lambda x: x.is_refused == True).write({'state': 'refused'})
        for key, item in res.items():
            sheet = self.browse(key)
            sheet.petty_cash_id.act_check_balance_to_close()
            item.write({'petty_cash_id': sheet.petty_cash_id.id})

        for sheet in self.filtered(lambda s: not s.accounting_date):
            sheet.accounting_date = sheet.account_move_id.date
        # In payment_mode  == petty_cash state must be post not done
        to_post = self.filtered(
            lambda sheet: sheet.payment_mode in ('own_account', 'petty_cash') and sheet.expense_line_ids)
        to_post.write({'state': 'post'})
        (self - to_post).write({'state': 'done'})
        self.activity_update()
        return res

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        if self.payment_mode != 'petty_cash':
            return {
                'name': _('Register Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': self.account_move_id.ids,
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        elif self.petty_cash_id.type == 'temporary':
            if self.clearance_type == 'account':
                return {
                    'name': _('Register Payment'),
                    'res_model': 'account.payment',
                    'view_mode': 'form',
                    'context': {
                        'default_is_petty_cash':True,
                        'default_amount': abs(self.payment_amount),
                        'default_journal_id': self.journal_id.id,
                        'default_payment_type': self.payment_amount > 0.0 and 'inbound' or 'outbound',
                        'default_partner_type': self.payment_amount > 0.0 and 'customer' or 'supplier',
                        'default_ref': self.name,
                        'default_partner_id': self.petty_cash_id.partner_id.id,
                        'default_destination_account_id': self.petty_cash_id.account_id.id,
                        'default_payment_petty_cash_id': self.id,
                        'skip_account_move_synchronization': True,
                        # 'default_is_petty_cash':True,
                        'default_petty_cash_id': self.petty_cash_id.id,
                    },
                    'target': 'current',
                    'type': 'ir.actions.act_window',
                }

            else:
                # TODO close this when hr modules is ready
                # raise ValidationError(
                #     _('the clearance type payroll not work.'))
                # TODO open this when hr modules is ready
                if self.salary_rule_id and self.employee_id.contract_id:
                    current_date = date.today()
                    month_start = date(current_date.year, current_date.month, 1)
                    month_end = date(current_date.year, current_date.month, calendar.mdays[current_date.month])
                    advantage = self.env['contract.advantage'].create({
                        'benefits_discounts': self.salary_rule_id.id,
                        'date_from': current_date,
                        'date_to': month_end,
                        'type': 'customize',
                        'amount': self.payment_amount,
                        'contract_advantage_id': self.employee_id.contract_id.id,
                    })
                    self.advantage_id = advantage.id
                elif not self.employee_id.contract_id:
                    raise ValidationError(_('You can not create in advantages when there is no contract.'))
                elif not self.salary_rule_id:
                    raise ValidationError(
                        _('You should select salary rule to move amount to advantages in employee contract '))
        elif self.petty_cash_id.type == 'continuous':
            if self.petty_cash_type == 'close':
                if self.clearance_type == 'account':
                    return {
                        'name': _('Register Payment'),
                        'res_model': 'account.payment',
                        'view_mode': 'form',
                        'context': {
                            'default_is_petty_cash': True,
                            'default_amount': abs(self.payment_amount),
                            'default_journal_id': self.journal_id.id,
                            'default_payment_type': self.payment_amount > 0.0 and 'inbound' or 'outbound',
                            'default_partner_type': self.payment_amount > 0.0 and 'customer' or 'supplier',
                            'default_ref': self.name,
                            'default_partner_id': self.petty_cash_id.partner_id.id,
                            'default_destination_account_id': self.petty_cash_id.account_id.id,
                            'default_payment_petty_cash_id': self.id,
                            'skip_account_move_synchronization': True,
                            # 'default_is_petty_cash':True,
                            'default_petty_cash_id': self.petty_cash_id.id,
                        },
                        'target': 'current',
                        'type': 'ir.actions.act_window',
                    }

                else:
                    # TODO close this when hr modules is ready
                    # raise ValidationError(
                    #     _('the clearance type payroll not work.'))
                    # TODO open this when hr modules is ready
                    if self.salary_rule_id and self.employee_id.contract_id:
                        current_date = date.today()
                        month_start = date(current_date.year, current_date.month, 1)
                        month_end = date(current_date.year, current_date.month, calendar.mdays[current_date.month])
                        advantage = self.env['contract.advantage'].create({
                            'benefits_discounts': self.salary_rule_id.id,
                            'date_from': current_date,
                            'date_to': month_end,
                            'type': 'customize',
                            'amount': self.payment_amount,
                            'contract_advantage_id': self.employee_id.contract_id.id,
                        })
                        self.advantage_id = advantage.id
                    elif not self.employee_id.contract_id:
                        raise ValidationError(_('You can not create in advantages when there is no contract.'))
                    elif not self.salary_rule_id:
                        raise ValidationError(
                            _('You should select salary rule to move amount to advantages in employee contract '))
                # Create vendor Bill With type petty cash
            if self.petty_cash_type == 'renew':
                return {
                'name': _('Renew Petty cash'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'context': {
                    'default_is_petty_cash': True,
                    'default_partner_id': self.petty_cash_id.partner_id.id,
                    'default_petty_cash_id': self.petty_cash_id.id,
                    'default_move_type': 'in_invoice',
                    'from_expense': True,
                },
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_open_invoice(self):
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('petty_cash_id', '=', self.petty_cash_id.id)],
            'context': {'default_move_type': 'in_invoice',
                        'default_is_petty_cash': True,
                        'default_partner_id': self.petty_cash_id.partner_id.id,
                        'default_petty_cash_id': self.petty_cash_id.id},
            'view_mode': 'tree,form',
        }

    def action_open_payments(self):
        return {
            'name': _('Payment'),
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [('payment_petty_cash_id', '=', self.id)],
            'flags': {'search_view': True, 'action_buttons': False},
        }
