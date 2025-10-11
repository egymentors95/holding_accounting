from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from lxml import etree
import json

class AccountMove(models.Model):
    _inherit = "account.move"

    is_petty_cash = fields.Boolean(
        string="Petty Cash", readonly=True, states={"draft": [("readonly", False)]},
    )
    petty_cash_id = fields.Many2one(
        comodel_name="petty.cash", readonly=True, states={"draft": [("readonly", False)]},
    )
    petty_cash_state = fields.Selection(related="petty_cash_id.state")
    transfer_amount = fields.Float(compute='_compute_transfer_amount', tracking=True)
    # amount_without_transfer = fields.Float(string='Origin amount',help='origin petty cash amount before Transfer',
    # tracking=True)
    transfer_expense_ids = fields.Many2many('hr.expense.sheet', string="Transfer From")

    @api.depends('transfer_expense_ids')
    def _compute_transfer_amount(self):
        for rec in self:
            rec.transfer_amount = sum(rec.transfer_expense_ids.mapped('payment_amount'))

    @api.onchange("partner_id")
    def _onchange_is_petty_cash(self):
        if not self._context.get('from_expense', False):
            self.petty_cash_id = self._context.get('default_petty_cash_id', False)

    @api.onchange("petty_cash_id")
    def _onchange_petty_cash_id(self):
        if self.petty_cash_id:
            self._check_temp_petty_cash()
            if not any(self.invoice_line_ids.mapped('petty_cash_id')):
                self.invoice_line_ids = self._add_petty_cash_invoice_line(self.petty_cash_id)
            self._onchange_invoice_line_ids()
            self._recompute_dynamic_lines()
            self.invoice_line_ids._onchange_price_subtotal()
            self._onchange_invoice_line_ids()
            if self.petty_cash_id.journal_id:
                # Prevent inconsistent journal_id
                if (
                        (
                                self.move_type in self.get_sale_types(include_receipts=True)
                                and self.petty_cash_id.journal_id.type == "sale"
                        )
                        or (
                        self.move_type in self.get_purchase_types(include_receipts=True)
                        and self.petty_cash_id.journal_id.type == "purchase"
                )
                        or (
                        self.move_type == "entry" and self.petty_cash_id.journal_id.type == "general"
                )
                ):
                    self.journal_id = self.petty_cash_id.journal_id.id

    def _check_temp_petty_cash(self):
        if self.petty_cash_id:
            rec_id = self.id
            try:
                rec_id = self._origin.id
            except:
                pass
            if self.move_type == 'in_invoice' and self.petty_cash_id.type == 'temporary' and \
                    self.search([('id', '!=', rec_id), ('move_type', '=', 'in_invoice'),
                                 ('petty_cash_id', '=', self.petty_cash_id.id), ('state', '=', 'posted')]):
                raise UserError(_("Temporary petty cash should pay only one time."))

    def action_post(self):
        self._check_temp_petty_cash()
        self._check_petty_cash_amount()
        return super().action_post()

    @api.constrains("invoice_line_ids", "line_ids")
    def _check_petty_cash_amount(self):
        for rec in self:
            petty_cash = rec.petty_cash_id
            if petty_cash and rec.invoice_line_ids:
                account = petty_cash.account_id
                # Must check Petty Cash on vender bills
                if (not rec.is_petty_cash and account.id in rec.invoice_line_ids.mapped(
                        "account_id").ids and rec.move_type in ['in_invoice', 'in_refund', 'out_refund']):
                    raise UserError(
                        _("Please check Petty Cash on {}.".format(rec.display_name))
                    )
                if rec.is_petty_cash:
                    if len(rec.invoice_line_ids) > 1:
                        print('xx...')
                        # raise UserError(
                        #     _(
                        #         "{} with petty cash checked must contain "
                        #         "only 1 line.".format(rec.display_name)
                        #     )
                        # )
                    # if rec.invoice_line_ids.account_id.id != account.id:
                    #     raise UserError(
                    #         _("Account on invoice line should be {}.".format(account.display_name))
                    #     )
                    balance = petty_cash.petty_cash_balance
                    limit = petty_cash.petty_cash_limit
                    max_amount = rec.move_type == 'in_invoice' and limit - balance or \
                                 rec.move_type == 'in_refund' and balance or \
                                 rec.move_type == 'out_refund' and abs(balance)

                    amount = sum(
                        rec.invoice_line_ids.filtered(
                            lambda l: l.account_id == account
                        ).mapped("price_subtotal")
                    )
                    company_currency = rec.company_id.currency_id
                    amount_company = rec.currency_id._convert(
                        amount,
                        company_currency,
                        rec.company_id,
                        rec.date or fields.Date.today(),
                    )
                    prec = rec.currency_id.rounding
                    if (float_compare(amount_company, max_amount, precision_rounding=prec) == 1):
                        raise ValidationError(
                            _(
                                "Petty Cash balance is %s %s.\n"
                                "Max amount to add is %s %s."
                            )
                            % (
                                "{:,.2f}".format(balance),
                                company_currency.symbol,
                                "{:,.2f}".format(max_amount),
                                company_currency.symbol,
                            )
                        )

    def _add_petty_cash_invoice_line(self, petty_cash):
        self.ensure_one()
        # Get suggested currency amount
        if self.env.context.get('active_model') == 'hr.expense.sheet':
            amount = self.env['hr.expense.sheet'].browse(self.env.context.get('active_id')).total_amount
        else:
            amount = self.move_type == 'in_invoice' and petty_cash.petty_cash_limit - petty_cash.petty_cash_balance or \
                     self.move_type == 'in_refund' and petty_cash.petty_cash_balance or \
                     self.move_type == 'out_refund' and abs(petty_cash.petty_cash_balance)

        company_currency = self.env.user.company_id.currency_id
        amount_doc_currency = company_currency._convert(
            amount, self.currency_id, self.company_id, self.date or fields.Date.today(),
        )

        inv_line = self.env["account.move.line"].new(
            {
                "name": petty_cash.account_id.name,
                "account_id": petty_cash.account_id.id,
                "partner_id": petty_cash.partner_id.id,
                "price_unit": amount_doc_currency,
                "quantity": 1,
                "petty_cash_id": petty_cash.id,
            }
        )
        return inv_line

    def action_register_payment(self):
        res = super(AccountMove, self).action_register_payment()
        res['context']['default_petty_cash_id'] = self.petty_cash_id.id
        return res
    #     todo start
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            print('move........................')
            context = {}
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res['arch'])
        my_group_gid = self.env.ref('hr_expense_petty_cash.group_petty_cash_user').id
        my_group_gid2 = self.env.ref('hr_expense_petty_cash.group_petty_cash_manager').id
        current_user_gids = self.env.user.groups_id.mapped('id')
        if  self._context.get('default_petty_cash_id')and (my_group_gid in current_user_gids and my_group_gid2 not in current_user_gids ):
            print('yes!!!!!!')
            if view_type == 'form':
                print('if-------')
                nodes = doc.xpath("//button[@name='action_post']")
                for node in doc.xpath("//button[@name='action_post']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='button_cancel']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                # for node in doc.xpath("//button[@name='action_vendor_eval']"):
                #     modifiers = json.loads(node.get("modifiers"))
                #     modifiers['invisible'] = True
                #     node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='action_reverse']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='button_draft']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
        if  self._context.get('default_petty_cash_id')and (my_group_gid in current_user_gids or my_group_gid2  in current_user_gids ):
            if view_type=='tree' or view_type=='form':
                print('teww..')
                #     create invoice from petty cash one time
                petty_cash_id = self.env['petty.cash'].search([('id','=',self._context.get('default_petty_cash_id'))])
                print('petty_cash_id = ',petty_cash_id)
                if petty_cash_id.invoice_count>=1:
                    print('if in con',petty_cash_id.invoice_count)
                    # if view_type == 'tree':
                    for node in doc.xpath("//tree"):
                        print('creayr falde')
                        node.set('create', 'false')
                    for node in doc.xpath("//form"):
                        print('creayr falde')
                        node.set('create', 'false')

            res['arch'] = etree.tostring(doc)
        return res
# add restricution for buttons in account move
# todo end


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_petty_cash_id = fields.Many2one("hr.expense.sheet", string="Petty cash")
    petty_cash_id = fields.Many2one(comodel_name="petty.cash")
    is_petty_cash = fields.Boolean(default =False)

    def _seek_for_lines(self):
        ''' add petty cash account line to counterpart_lines in case of payment create from petty cash
        '''
        liquidity_lines, counterpart_lines, writeoff_lines = super()._seek_for_lines()
        petty_cash_lines = self.env['account.move.line']
        if self.payment_petty_cash_id:
            for line in self.move_id.line_ids:
                if line.account_id.internal_type in ('other'):
                    petty_cash_lines += line
                counterpart_lines += petty_cash_lines
        return liquidity_lines, counterpart_lines, writeoff_lines

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    def _compute_destination_account_id(self):
        if self.payment_petty_cash_id:
            self.destination_account_id = self.payment_petty_cash_id.petty_cash_id.account_id.id
        else:
            return super()._compute_destination_account_id()

    def action_post(self):
        ''' update petty cash expenses state '''
        for rec in self:
            if rec.payment_petty_cash_id:
                rec.payment_petty_cash_id.write({'state': 'done'})
            if rec.petty_cash_id:
                rec.petty_cash_id.write({'is_paid': True})
        return super().action_post()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' inherit to add petty_cash_id in move line
        '''
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        for rec in line_vals_list:
            if self.payment_petty_cash_id and rec[
                'account_id'] == self.payment_petty_cash_id.petty_cash_id.account_id.id:
                rec['petty_cash_id'] = self.payment_petty_cash_id.petty_cash_id.id
        return line_vals_list
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            print('payment........................')
            context = {}
        res = super(AccountPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res['arch'])
        my_group_gid = self.env.ref('hr_expense_petty_cash.group_petty_cash_user').id
        my_group_gid2 = self.env.ref('hr_expense_petty_cash.group_petty_cash_manager').id
        current_user_gids = self.env.user.groups_id.mapped('id')
        if  self._context.get('default_petty_cash_id')and (my_group_gid in current_user_gids and my_group_gid2 not in current_user_gids ):
            print('yes!!!!!!')
            if view_type == 'form':
                print('if-------')
                nodes = doc.xpath("//button[@name='action_post']")
                for node in doc.xpath("//button[@name='action_post']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='action_cancel']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                for node in doc.xpath("//button[@name='mark_as_sent']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='unmark_as_sent']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//button[@name='action_draft']"):
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['invisible'] = True
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res
#

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    petty_cash_id = fields.Many2one(comodel_name="petty.cash", readonly=True)
