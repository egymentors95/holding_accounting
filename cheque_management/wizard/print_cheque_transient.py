# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoicePrintBankChequeWizard(models.TransientModel):
    _name = 'invoice.print.bank.cheque.wizard'
    _description = 'Print Bank Cheque Wizard'


    @api.depends('amount', 'currency_id')
    def _get_amount_in_words(self):
        self.amount_in_words = self.currency_id and self.currency_id.amount_to_text(self.amount) or ''

    name = fields.Char(
        related="partner_id.name", string="Name"
    )
    issue_place = fields.Char(
        string="Place of Issue"
    )
    reason = fields.Char(
        string="Reason of Issue"
    )
    ac_pay_visible = fields.Boolean(
        string="A/C Pay To",default=True
    )
    partner_id = fields.Many2one(
        "res.partner", "Vendor"
    )
    pay_name_line1 = fields.Char("Pay To")
    pay_name_line2 = fields.Char("Pay To Line2")
    currency_id = fields.Many2one("res.currency")
    amount = fields.Float("Amount")
    amount_in_words = fields.Char(
        string="Amount In Words",
        compute="_get_amount_in_words"
    )
    amount_in_words_line2 = fields.Char("Amount In Words Line 2",)
    date = fields.Date(
        string="Date On Cheque",
        default=fields.Date.today()
    )
    cheque_book_id = fields.Many2one(
        "bank.cheque.book", "Cheque Book"
    )
    cheque_history_id = fields.Many2one(
        "issued.bank.cheque.history", "Cheque Number",
        domain='[("issued", "=", False), ("bank_cheque_book_id", "=", cheque_book_id)]'
    )
    cheque_has_pay_line2 = fields.Boolean(
        compute="_check_cheque_attributes"
    )
    cheque_has_amount_line2 = fields.Boolean(
        compute="_check_cheque_attributes"
    )
    is_preview = fields.Boolean("Preview")

    @api.depends("cheque_book_id")
    def _check_cheque_attributes(self):
        self.cheque_has_pay_line2 = False
        self.cheque_has_amount_line2 = False
        if self.cheque_book_id:
            for bank_cheque_attr in self.cheque_book_id.bank_cheque_id.cheque_attribute_line_ids.filtered(lambda o: o.name.attribute in ['pay_line2', 'amount_line_2']):
                if bank_cheque_attr.name.attribute == "pay_line2":
                    self.cheque_has_pay_line2 = True
                if bank_cheque_attr.name.attribute == "amount_line_2":
                    self.cheque_has_amount_line2 = True


    @api.onchange("amount")
    def onchange_amount(self):
        if self.currency_id:
            self.amount_in_words_line2 = False
            self.amount_in_words = self.currency_id.amount_to_text(self.amount)
            self.amount_in_words = str(self.amount_in_words).replace('،',' و')
            self.set_amount_lines_in_word()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.pay_name_line1 = self.partner_id.name

    @api.onchange("cheque_book_id")
    def onchange_cheque_book_id(self):
        if self.cheque_book_id:
            self.onchange_amount()
            x = self.env["issued.bank.cheque.history"].search(
                [("bank_cheque_book_id", "=", self.cheque_book_id.id), ("issued", "=", False),
                 ('state', '!=', 'cancelled')], order="cheque_number asc", limit=1)
            if x:
                self.cheque_history_id = x.id
            return {
                'domain': {
                    'cheque_history_id': [('bank_cheque_book_id', '=', self.cheque_book_id.id)]
                }
            }
        return {}

    def set_amount_lines_in_word(self):
        self.ensure_one()
        if self.amount_in_words:
            if self.cheque_book_id.bank_cheque_id.max_char_in_line1:
                # char_count = len(self.amount_in_words)
                raw_str = self.amount_in_words
                # max_char = self.cheque_book_id.max_char_in_line1
                line1 = ""
                line2 = ""
                total_word = 0
                for word in raw_str.split(" "):
                    if total_word + len(word) <= self.cheque_book_id.bank_cheque_id.max_char_in_line1:
                        total_word += len(word) + 1
                        line1 += word
                        line1 += " "
                    else:
                        line2 = raw_str[total_word:]
                        break
                self.amount_in_words = line1
                self.amount_in_words_line2 = line2
    def print_cheque_preview(self):
        self.ensure_one()
        self.is_preview = True
        return self.env.ref('cheque_management.bank_cheque_leaf_print_report').report_action(self)

    def print_cheque(self):
        self.ensure_one()
        self.is_preview = False
        if self.cheque_history_id.issued:
            raise UserError(_("Cheque has been already printed with Cheque number %s" %
                              self.cheque_history_id.cheque_number))
        self.cheque_history_id.write({
            "customer_id": self.partner_id.id if self.partner_id else False,
            "issue_date": fields.Date.today(),
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "issued": True,
            "paid_to": self.pay_name_line1,
            "state": "printed"
        })
        if self._context.get("active_model") == "account.payment":
            payment_id = self.env["account.payment"].browse(self._context.get("active_id"))
            payment_id.write({'cheque_history_id':self.cheque_history_id.id})
        return self.env.ref('cheque_management.bank_cheque_leaf_print_report').report_action(self)
