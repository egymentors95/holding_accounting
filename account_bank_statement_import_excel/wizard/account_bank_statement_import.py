import logging
import re
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.addons.base_iban.models.res_partner_bank import _map_iban_template
from odoo.addons.base_iban.models.res_partner_bank import validate_iban
from odoo.tools import float_compare, float_round, float_repr

from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug("xlrd not found.")


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _check_journal_bank_account(self, journal, account_number):
        return journal.bank_account_id.sanitized_acc_number == account_number

        res = super(
            AccountBankStatementImport, self
        )._check_journal_bank_account(journal, account_number)
        if not res:
            e_acc_num = journal.bank_account_id.sanitized_acc_number
            e_acc_num = e_acc_num.replace(" ", "")
            validate_iban(e_acc_num)
            country_code = e_acc_num[:2].lower()
            iban_template = _map_iban_template[country_code].replace(
                " ", "")
            e_acc_num = "".join(
                [c for c, t in zip(e_acc_num, iban_template) if t == "C"])
            res = (e_acc_num == account_number)
        return res

    @api.model
    def _check_excel(self, data_file):
        try:
            excel = xlrd.open_workbook(file_contents=data_file)
        except Exception as e:
            _logger.debug(e)
            return False
        return excel

    @api.model
    def _prepare_ofx_transaction_line(self, transaction):
        # Since ofxparse doesn't provide account numbers,
        # we cannot provide the key 'bank_account_id',
        # nor the key 'account_number'
        # If you read odoo10/addons/account_bank_statement_import/
        # account_bank_statement_import.py, it's the only 2 keys
        # we can provide to match a partner.
        vals = {
            'date': transaction.date,
            'name': transaction.payee + (
                    transaction.memo and ': ' + transaction.memo or ''),
            'ref': transaction.id,
            'amount': float(transaction.amount),
            'unique_import_id': transaction.id,
        }
        return vals

    def _get_excel_data(self, excel_file, excel_conf):
        xl_sheet = excel_file.sheet_by_index(0)
        journal = self.env['account.journal'].browse(self.env.context.get('journal_id', []))
        currency = journal.currency_id.name

        account_number = not excel_conf.details_only and \
                         xl_sheet.cell(excel_conf.account_number_row, excel_conf.account_number_col).value or \
                         journal.bank_account_id.acc_number
        # got to fix currency problem but for now gonna use company currency

        start = not excel_conf.details_only and \
                xl_sheet.cell(excel_conf.balance_start_row, excel_conf.balance_start_col).value or 0

        balance_start = isinstance(start, str) and float(re.sub('[^.\-\d]', '', start.split()[0])) or start

        end = not excel_conf.details_only and \
              xl_sheet.cell(excel_conf.balance_end_row, excel_conf.balance_end_col).value or 0

        balance_end = isinstance(start, str) and float(re.sub('[^.\-\d]', '', end.split()[0])) or end

        lines = []

        details_row = excel_conf.details_row
        total_amt = 0.0

        while True:
            try:
                debit = float(xl_sheet.cell(details_row, excel_conf.debit_col).value or 0)
                credit = float(xl_sheet.cell(details_row, excel_conf.credit_col).value or 0)
                # balance = float(xl_sheet.cell(details_row, excel_conf.balance_col).value or 0)

                type = xl_sheet.cell(details_row, excel_conf.type_col).value
                note = xl_sheet.cell(details_row, excel_conf.note_col).value
                date = xl_sheet.cell(details_row, excel_conf.date_col).value
                date = datetime.strptime(date, excel_conf.date_format or "%d/%m/%Y")
                amount = credit and credit or (excel_conf.debit_sign and -1 * debit or debit)
                total_amt += amount
                lines.append({'amount': amount,
                              # 'balance': balance,
                              'payment_ref': type + ' ' + note,
                              'date': date})
                details_row += 1
            except:
                break
        vals_bank_statement = {
            'name': account_number,
            'transactions': lines,
            'balance_start': balance_start,
            'balance_end_real': balance_end,
        }
        return (currency, account_number, [vals_bank_statement])

    def _parse_file(self, data_file):
        excel = self._check_excel(data_file)
        if not excel:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

        transactions = []
        total_amt = 0.00
        try:
            journal = self.env['account.journal'].browse(self.env.context.get('journal_id', []))
            if not journal.excel_dimension:
                raise UserError(_("Determine excel dimension for this journal. "))
            excel_data = self._get_excel_data(excel, journal.excel_dimension)
            return excel_data
            # for transaction in ofx.account.statement.transactions:
            #     vals = self._prepare_ofx_transaction_line(transaction)
            #     if vals:
            #         transactions.append(vals)
            #         total_amt += vals['amount']
        except Exception as e:
            raise UserError(_(
                "The following problem occurred during import. "
                "The file might not be valid.\n\n %s") % e)

        # balance = float(ofx.account.statement.balance)
        # vals_bank_statement = {
        #     'name': ofx.account.number,
        #     'transactions': transactions,
        #     'balance_start': balance - total_amt,
        #     'balance_end_real': balance,
        # }
        return ofx.account.statement.currency, ofx.account.number, [vals_bank_statement]


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def get_reconciliation_proposition(self, excluded_ids=None):
        """ Returns move lines that constitute the best guess to reconcile a statement line
            Note: it only looks for move lines in the same currency as the statement line.
        """
        self.ensure_one()
        if not excluded_ids:
            excluded_ids = []
        amount = self.amount_currency or self.amount
        company_currency = self.journal_id.company_id.currency_id
        st_line_currency = self.currency_id or self.journal_id.currency_id
        currency = (st_line_currency and st_line_currency !=
                    company_currency) and st_line_currency.id or False
        precision = st_line_currency and st_line_currency.decimal_places or company_currency.decimal_places
        params = {'company_id': self.env.user.company_id.id,
                  'account_payable_receivable': (self.journal_id.default_credit_account_id.id, self.journal_id.default_debit_account_id.id),
                  'amount': float_repr(float_round(amount, precision_digits=precision), precision_digits=precision),
                  'partner_id': self.partner_id.id,
                  'excluded_ids': tuple(excluded_ids),
                  'ref': self.name,
                  }
        # Look for structured communication match
        if self.name:
            add_to_select = ", CASE WHEN aml.ref = %(ref)s THEN 1 ELSE 2 END as temp_field_order "
            add_to_from = " JOIN account_move m ON m.id = aml.move_id "
            select_clause, from_clause, where_clause = self._get_common_sql_query(
                overlook_partner=True, excluded_ids=excluded_ids, split=True)
            sql_query = select_clause + add_to_select + from_clause + add_to_from + where_clause
            sql_query += " AND (aml.ref= %(ref)s or m.name = %(ref)s) \
                    ORDER BY temp_field_order, date_maturity desc, aml.id desc"
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchone()
            if results:
                return self.env['account.move.line'].browse(results[0])

        # Look for a single move line with the same amount
        field = currency and 'amount_residual_currency' or 'amount_residual'
        liquidity_field = currency and 'amount_currency' or amount > 0 and 'aml.debit' or 'aml.credit'
        liquidity_amt_clause = currency and '%(amount)s::numeric' or 'abs(%(amount)s::numeric)'
        sql_query = self._get_common_sql_query(excluded_ids=excluded_ids) + \
                    " AND (" + field + " = %(amount)s::numeric OR (acc.internal_type = 'liquidity' AND " + liquidity_field + " = " + liquidity_amt_clause + ")) \
                ORDER BY date_maturity desc, aml.id desc LIMIT 1"
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.fetchone()
        if results:
            return self.env['account.move.line'].browse(results[0])

        return self.env['account.move.line']

    def auto_reconcile(self):
        """ Try to automatically reconcile the statement.line ; return the counterpart journal entry/ies if the automatic reconciliation succeeded, False otherwise.
            TODO : this method could be greatly improved and made extensible
        """
        self.ensure_one()
        match_recs = self.env['account.move.line']

        amount = self.amount_currency or self.amount
        company_currency = self.journal_id.company_id.currency_id
        st_line_currency = self.currency_id or self.journal_id.currency_id
        currency = (st_line_currency and st_line_currency !=
                    company_currency) and st_line_currency.id or False
        precision = st_line_currency and st_line_currency.decimal_places or company_currency.decimal_places
        params = {'company_id': self.env.user.company_id.id,
                  'account_payable_receivable': (self.journal_id.default_credit_account_id.id, self.journal_id.default_debit_account_id.id),
                  'amount': float_round(amount, precision_digits=precision),
                  'partner_id': self.partner_id.id,
                  'ref': self.name,
                  }
        field = currency and 'amount_residual_currency' or 'amount_residual'
        liquidity_field = currency and 'amount_currency' or amount > 0 and 'aml.debit' or 'aml.credit'
        # Look for structured communication match
        if self.name:
            sql_query = self._get_common_sql_query() + " AND aml.ref = %(ref)s AND (" + field + \
                        " = %(amount)s OR (acc.internal_type = 'liquidity' AND " + liquidity_field + " = %(amount)s)) \
                ORDER BY date_maturity asc, aml.id asc"
            self.env.cr.execute(sql_query, params)
            match_recs = self.env.cr.dictfetchall()
            if len(match_recs) > 1:
                return False

        # Look for a single move line with the same partner, the same amount
        if not match_recs:
            if self.partner_id:
                sql_query = self._get_common_sql_query(
                ) + " AND (" + field + " = %(amount)s OR (acc.internal_type = 'liquidity' AND " + liquidity_field + " = %(amount)s)) \
                ORDER BY date_maturity asc, aml.id asc"
                self.env.cr.execute(sql_query, params)
                match_recs = self.env.cr.dictfetchall()
                if len(match_recs) > 1:
                    return False

        if not match_recs:
            return False

        match_recs = self.env['account.move.line'].browse([aml.get('id') for aml in match_recs])
        # Now reconcile
        counterpart_aml_dicts = []
        payment_aml_rec = self.env['account.move.line']
        for aml in match_recs:
            if aml.account_id.internal_type == 'liquidity':
                payment_aml_rec = (payment_aml_rec | aml)
            else:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
                counterpart_aml_dicts.append({
                    'name': aml.name if aml.name != '/' else aml.move_id.name,
                    'debit': amount < 0 and -amount or 0,
                    'credit': amount > 0 and amount or 0,
                    'move_line': aml
                })

        try:
            with self._cr.savepoint():
                counterpart = self.process_reconciliation(
                    counterpart_aml_dicts=counterpart_aml_dicts,
                    payment_aml_rec=payment_aml_rec)
            return counterpart
        except UserError:
            # A configuration / business logic error that makes it impossible to auto-reconcile should not be raised
            # since automatic reconciliation is just an amenity and the user will get the same exception when manually
            # reconciling. Other types of exception are (hopefully) programmation errors and should cause a stacktrace.
            self.invalidate_cache()
            self.env['account.move'].invalidate_cache()
            self.env['account.move.line'].invalidate_cache()
            return False
