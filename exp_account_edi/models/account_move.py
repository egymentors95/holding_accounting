# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import frozendict
from contextlib import contextmanager
from freezegun import freeze_time
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_base_affected = fields.Boolean(
        string="Base Affected by Previous Taxes",
        default=True,
        help="If set, taxes with a lower sequence might affect this one, provided they try to do it.")
    

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _collect_tax_cash_basis_values(self):
        ''' Collect all information needed to create the tax cash basis journal entries:
        - Determine if a tax cash basis journal entry is needed.
        - Compute the lines to be processed and the amounts needed to compute a percentage.
        :return: A dictionary:
            * move:                     The current account.move record passed as parameter.
            * to_process_lines:         A tuple (caba_treatment, line) where:
                                            - caba_treatment is either 'tax' or 'base', depending on what should
                                              be considered on the line when generating the caba entry.
                                              For example, a line with tax_ids=caba and tax_line_id=non_caba
                                              will have a 'base' caba treatment, as we only want to treat its base
                                              part in the caba entry (the tax part is already exigible on the invoice)

                                            - line is an account.move.line record being not exigible on the tax report.
            * currency:                 The currency on which the percentage has been computed.
            * total_balance:            sum(payment_term_lines.mapped('balance').
            * total_residual:           sum(payment_term_lines.mapped('amount_residual').
            * total_amount_currency:    sum(payment_term_lines.mapped('amount_currency').
            * total_residual_currency:  sum(payment_term_lines.mapped('amount_residual_currency').
            * is_fully_paid:            A flag indicating the current move is now fully paid.
        '''
        self.ensure_one()

        values = {
            'move': self,
            'to_process_lines': [],
            'total_balance': 0.0,
            'total_residual': 0.0,
            'total_amount_currency': 0.0,
            'total_residual_currency': 0.0,
        }

        currencies = set()
        has_term_lines = False
        for line in self.line_ids:
            if line.account_internal_type in ('receivable', 'payable'):
                sign = 1 if line.balance > 0.0 else -1

                currencies.add(line.currency_id)
                has_term_lines = True
                values['total_balance'] += sign * line.balance
                values['total_residual'] += sign * line.amount_residual
                values['total_amount_currency'] += sign * line.amount_currency
                values['total_residual_currency'] += sign * line.amount_residual_currency

            elif line.tax_line_id.tax_exigibility == 'on_payment':
                values['to_process_lines'].append(('tax', line))
                currencies.add(line.currency_id)

            elif 'on_payment' in line.tax_ids.flatten_taxes_hierarchy().mapped('tax_exigibility'):
                values['to_process_lines'].append(('base', line))
                currencies.add(line.currency_id)

        if not values['to_process_lines'] or not has_term_lines:
            return None

        # Compute the currency on which made the percentage.
        if len(currencies) == 1:
            values['currency'] = list(currencies)[0]
        else:
            # Don't support the case where there is multiple involved currencies.
            return None

        # Determine whether the move is now fully paid.
        values['is_fully_paid'] = self.company_id.currency_id.is_zero(values['total_residual']) \
                                  or values['currency'].is_zero(values['total_residual_currency'])

        return values

    @api.depends('line_ids.account_id.internal_type')
    def _compute_always_tax_exigible(self):
        for record in self:
            # We need to check is_invoice as well because always_tax_exigible is used to
            # set the tags as well, during the encoding. So, if no receivable/payable
            # line has been created yet, the invoice would be detected as always exigible,
            # and set the tags on some lines ; which would be wrong.
            record.always_tax_exigible = not record.is_invoice(True) \
                                         and not record._collect_tax_cash_basis_values()

    always_tax_exigible = fields.Boolean(
        compute='_compute_always_tax_exigible',
        store=True,
        readonly=False,
        help="Technical field used by cash basis taxes, telling the lines of the move are always exigible. "
             "This happens if the move contains no payable or receivable line.")

    edi_document_ids = fields.One2many(
        comodel_name='account.edi.document',
        inverse_name='move_id')
    edi_state = fields.Selection(
        selection=[('to_send', 'To Send'), ('sent', 'Sent'), ('to_cancel', 'To Cancel'), ('cancelled', 'Cancelled')],
        string="Electronic invoicing",
        store=True,
        compute='_compute_edi_state',
        help='The aggregated state of all the EDIs with web-service of this move')
    edi_error_count = fields.Integer(
        compute='_compute_edi_error_count',
        help='How many EDIs are in error for this move ?')
    edi_blocking_level = fields.Selection(
        selection=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error')],
        compute='_compute_edi_error_message')
    edi_error_message = fields.Html(
        compute='_compute_edi_error_message')
    edi_web_services_to_process = fields.Text(
        compute='_compute_edi_web_services_to_process',
        help="Technical field to display the documents that will be processed by the CRON")
    edi_show_cancel_button = fields.Boolean(
        compute='_compute_edi_show_cancel_button')
    edi_show_abandon_cancel_button = fields.Boolean(
        compute='_compute_edi_show_abandon_cancel_button')

    @api.depends('edi_document_ids.state')
    def _compute_edi_state(self):
        for move in self:
            all_states = set(move.edi_document_ids.filtered(lambda d: d.edi_format_id._needs_web_services()).mapped('state'))
            if all_states == {'sent'}:
                move.edi_state = 'sent'
            elif all_states == {'cancelled'}:
                move.edi_state = 'cancelled'
            elif 'to_send' in all_states:
                move.edi_state = 'to_send'
            elif 'to_cancel' in all_states:
                move.edi_state = 'to_cancel'
            else:
                move.edi_state = False
    def _action_invoice_ready_to_be_sent(self):
        """ Hook allowing custom code when an invoice becomes ready to be sent by mail to the customer.
        For example, when an EDI document must be sent to the government and be signed by it.
        """
        pass

    # def _is_ready_to_be_sent(self):
    #     """ Helper telling if a journal entry is ready to be sent by mail to the customer.

    #     :return: True if the invoice is ready, False otherwise.
    #     """
    #     self.ensure_one()
    #     return True

    @contextmanager
    def _send_only_when_ready(self):
        moves_not_ready = self.filtered(lambda x: not x._is_ready_to_be_sent())

        try:
            yield
        finally:
            moves_now_ready = moves_not_ready.filtered(lambda x: x._is_ready_to_be_sent())
            if moves_now_ready:
                moves_now_ready._action_invoice_ready_to_be_sent()
    @api.depends('edi_document_ids.error')
    def _compute_edi_error_count(self):
        for move in self:
            move.edi_error_count = len(move.edi_document_ids.filtered(lambda d: d.error))

    @api.depends('edi_error_count', 'edi_document_ids.error', 'edi_document_ids.blocking_level')
    def _compute_edi_error_message(self):
        for move in self:
            if move.edi_error_count == 0:
                move.edi_error_message = None
                move.edi_blocking_level = None
            elif move.edi_error_count == 1:
                error_doc = move.edi_document_ids.filtered(lambda d: d.error)
                move.edi_error_message = error_doc.error
                move.edi_blocking_level = error_doc.blocking_level
            else:
                error_levels = set([doc.blocking_level for doc in move.edi_document_ids])
                if 'error' in error_levels:
                    move.edi_error_message = str(move.edi_error_count) + _(" Electronic invoicing error(s)")
                    move.edi_blocking_level = 'error'
                elif 'warning' in error_levels:
                    move.edi_error_message = str(move.edi_error_count) + _(" Electronic invoicing warning(s)")
                    move.edi_blocking_level = 'warning'
                else:
                    move.edi_error_message = str(move.edi_error_count) + _(" Electronic invoicing info(s)")
                    move.edi_blocking_level = 'info'

    @api.depends(
        'edi_document_ids',
        'edi_document_ids.state',
        'edi_document_ids.blocking_level',
        'edi_document_ids.edi_format_id',
        'edi_document_ids.edi_format_id.name')
    def _compute_edi_web_services_to_process(self):
        for move in self:
            to_process = move.edi_document_ids.filtered(lambda d: d.state in ['to_send', 'to_cancel'] and d.blocking_level != 'error')
            format_web_services = to_process.edi_format_id.filtered(lambda f: f._needs_web_services())
            move.edi_web_services_to_process = ', '.join(f.name for f in format_web_services)

    @api.depends(
        'state',
        'edi_document_ids.state')
    def _compute_show_reset_to_draft_button(self):
        # OVERRIDE
        super()._compute_show_reset_to_draft_button()

        for move in self:
            for doc in move.edi_document_ids:
                if doc.edi_format_id._needs_web_services() \
                        and doc.state in ('sent', 'to_cancel') \
                        and move.is_invoice(include_receipts=True) \
                        and doc.edi_format_id._is_required_for_invoice(move):
                    move.show_reset_to_draft_button = False
                    break

    @api.depends(
        'state',
        'edi_document_ids.state')
    def _compute_edi_show_cancel_button(self):
        for move in self:
            if move.state != 'posted':
                move.edi_show_cancel_button = False
                continue

            move.edi_show_cancel_button = any([doc.edi_format_id._needs_web_services()
                                               and doc.state == 'sent'
                                               and move.is_invoice(include_receipts=True)
                                               and doc.edi_format_id._is_required_for_invoice(move)
                                              for doc in move.edi_document_ids])

    @api.depends(
        'state',
        'edi_document_ids.state')
    def _compute_edi_show_abandon_cancel_button(self):
        for move in self:
            move.edi_show_abandon_cancel_button = any(doc.edi_format_id._needs_web_services()
                                                      and doc.state == 'to_cancel'
                                                      and move.is_invoice(include_receipts=True)
                                                      and doc.edi_format_id._is_required_for_invoice(move)
                                                      for doc in move.edi_document_ids)

    ####################################################
    # Export Electronic Document
    ####################################################

    @api.model
    def _add_edi_tax_values(self, results, grouping_key, serialized_grouping_key, tax_values, key_by_tax=None):
        # Add to global results.
        results['tax_amount'] += tax_values['tax_amount']
        results['tax_amount_currency'] += tax_values['tax_amount_currency']
        # Add to tax details.
        if serialized_grouping_key not in results['tax_details']:
            tax_details = results['tax_details'][serialized_grouping_key]
            tax_details.update(grouping_key)
            tax_details.update({
                'base_amount': tax_values['base_amount'],
                'base_amount_currency': tax_values['base_amount_currency'],
            })
        else:
            tax_details = results['tax_details'][serialized_grouping_key]
            if key_by_tax:
                add_to_base_amount = key_by_tax[tax_values['tax_id']] != key_by_tax.get(tax_values['src_line_id'].tax_line_id)
            else:
                add_to_base_amount = tax_values['base_line_id'] not in set(x['base_line_id'] for x in tax_details['group_tax_details'])
            if add_to_base_amount:
                tax_details['base_amount'] += tax_values['base_amount']
                tax_details['base_amount_currency'] += tax_values['base_amount_currency']
        tax_details['tax_amount'] += tax_values['tax_amount']
        tax_details['tax_amount_currency'] += tax_values['tax_amount_currency']
        tax_details['exemption_reason'] = tax_values['tax_id'].name
        tax_details['group_tax_details'].append(tax_values)

    def _prepare_edi_tax_details(self, filter_to_apply=None, filter_invl_to_apply=None, grouping_key_generator=None, compute_mode='tax_details'):
        ''' Compute amounts related to taxes for the current invoice.

        :param filter_to_apply:         Optional filter to exclude some tax values from the final results.
                                        The filter is defined as a method getting a dictionary as parameter
                                        representing the tax values for a single repartition line.
                                        This dictionary contains:

            'base_line_id':             An account.move.line record.
            'tax_id':                   An account.tax record.
            'tax_repartition_line_id':  An account.tax.repartition.line record.
            'base_amount':              The tax base amount expressed in company currency.
            'tax_amount':               The tax amount expressed in company currency.
            'base_amount_currency':     The tax base amount expressed in foreign currency.
            'tax_amount_currency':      The tax amount expressed in foreign currency.

                                        If the filter is returning False, it means the current tax values will be
                                        ignored when computing the final results.

        :param filter_invl_to_apply:    Optional filter to exclude some invoice lines.

        :param grouping_key_generator:  Optional method used to group tax values together. By default, the tax values
                                        are grouped by tax. This parameter is a method getting a dictionary as parameter
                                        (same signature as 'filter_to_apply').

                                        This method must returns a dictionary where values will be used to create the
                                        grouping_key to aggregate tax values together. The returned dictionary is added
                                        to each tax details in order to retrieve the full grouping_key later.

        :param compute_mode:            Optional parameter to specify the method used to allocate the tax line amounts
                                        among the invoice lines:
                                        'tax_details' (the default) uses the AccountMove._get_query_tax_details method.
                                        'compute_all' uses the AccountTax._compute_all method.

                                        The 'tax_details' method takes the tax line balance and allocates it among the
                                        invoice lines to which that tax applies, proportionately to the invoice lines'
                                        base amounts. This always ensures that the sum of the tax amounts equals the
                                        tax line's balance, which, depending on the constraints of a particular
                                        localization, can be more appropriate when 'Round Globally' is set.

                                        The 'compute_all' method returns, for each invoice line, the exact tax amounts
                                        corresponding to the taxes applied to the invoice line. Depending on the
                                        constraints of the particular localization, this can be more appropriate when
                                        'Round per Line' is set.

        :return:                        The full tax details for the current invoice and for each invoice line
                                        separately. The returned dictionary is the following:

            'base_amount':              The total tax base amount in company currency for the whole invoice.
            'tax_amount':               The total tax amount in company currency for the whole invoice.
            'base_amount_currency':     The total tax base amount in foreign currency for the whole invoice.
            'tax_amount_currency':      The total tax amount in foreign currency for the whole invoice.
            'tax_details':              A mapping of each grouping key (see 'grouping_key_generator') to a dictionary
                                        containing:

                'base_amount':              The tax base amount in company currency for the current group.
                'tax_amount':               The tax amount in company currency for the current group.
                'base_amount_currency':     The tax base amount in foreign currency for the current group.
                'tax_amount_currency':      The tax amount in foreign currency for the current group.
                'group_tax_details':        The list of all tax values aggregated into this group.

            'invoice_line_tax_details': A mapping of each invoice line to a dictionary containing:

                'base_amount':          The total tax base amount in company currency for the whole invoice line.
                'tax_amount':           The total tax amount in company currency for the whole invoice line.
                'base_amount_currency': The total tax base amount in foreign currency for the whole invoice line.
                'tax_amount_currency':  The total tax amount in foreign currency for the whole invoice line.
                'tax_details':          A mapping of each grouping key (see 'grouping_key_generator') to a dictionary
                                        containing:

                    'base_amount':          The tax base amount in company currency for the current group.
                    'tax_amount':           The tax amount in company currency for the current group.
                    'base_amount_currency': The tax base amount in foreign currency for the current group.
                    'tax_amount_currency':  The tax amount in foreign currency for the current group.
                    'group_tax_details':    The list of all tax values aggregated into this group.

        '''
        self.ensure_one()

        def default_grouping_key_generator(tax_values):
            return {'tax': tax_values['tax_id']}

        def compute_invoice_lines_tax_values_dict_from_tax_details(invoice_lines):
            invoice_lines_tax_values_dict = defaultdict(list)
            tax_details_query, tax_details_params = invoice_lines._get_query_tax_details_from_domain([('move_id', '=', self.id)])
            self._cr.execute(tax_details_query, tax_details_params)
            for row in self._cr.dictfetchall():
                invoice_line = invoice_lines.browse(row['base_line_id'])
                tax_line = invoice_lines.browse(row['tax_line_id'])
                src_line = invoice_lines.browse(row['src_line_id'])
                tax = self.env['account.tax'].browse(row['tax_id'])
                src_tax = self.env['account.tax'].browse(row['group_tax_id']) if row['group_tax_id'] else tax

                invoice_lines_tax_values_dict[invoice_line].append({
                    'base_line_id': invoice_line,
                    'tax_line_id': tax_line,
                    'src_line_id': src_line,
                    'tax_id': tax,
                    'src_tax_id': src_tax,
                    'tax_repartition_line_id': tax_line.tax_repartition_line_id,
                    'base_amount': row['base_amount'],
                    'tax_amount': row['tax_amount'],
                    'base_amount_currency': row['base_amount_currency'],
                    'tax_amount_currency': row['tax_amount_currency'],
                })
            return invoice_lines_tax_values_dict

        def compute_invoice_lines_tax_values_dict_from_compute_all(invoice_lines):
            invoice_lines_tax_values_dict = {}
            sign = -1 if self.is_inbound() else 1
            for invoice_line in invoice_lines:
                taxes_res = invoice_line.tax_ids.compute_all(
                    invoice_line.price_unit * (1 - (invoice_line.discount / 100.0)),
                    currency=invoice_line.currency_id,
                    quantity=invoice_line.quantity,
                    product=invoice_line.product_id,
                    partner=invoice_line.partner_id,
                    is_refund=invoice_line.move_id.move_type in ('in_refund', 'out_refund'),
                )
                invoice_lines_tax_values_dict[invoice_line] = []
                rate = abs(invoice_line.balance) / abs(invoice_line.amount_currency) if invoice_line.amount_currency else 0.0
                for tax_res in taxes_res['taxes']:
                    tax_amount = tax_res['amount'] * rate
                    if self.company_id.tax_calculation_rounding_method == 'round_per_line':
                        tax_amount = invoice_line.company_currency_id.round(tax_amount)
                    invoice_lines_tax_values_dict[invoice_line].append({
                        'base_line_id': invoice_line,
                        'tax_id': self.env['account.tax'].browse(tax_res['id']),
                        'tax_repartition_line_id': self.env['account.tax.repartition.line'].browse(tax_res['tax_repartition_line_id']),
                        'base_amount': sign * invoice_line.company_currency_id.round(tax_res['base'] * rate),
                        'tax_amount': sign * tax_amount,
                        'base_amount_currency': sign * tax_res['base'],
                        'tax_amount_currency': sign * tax_res['amount'],
                    })
            return invoice_lines_tax_values_dict

        # Compute the taxes values for each invoice line.
        invoice_lines = self.invoice_line_ids.filtered(lambda line: not line.display_type)
        if filter_invl_to_apply:
            invoice_lines = invoice_lines.filtered(filter_invl_to_apply)

        if compute_mode == 'compute_all':
            invoice_lines_tax_values_dict = compute_invoice_lines_tax_values_dict_from_compute_all(invoice_lines)
        else:
            invoice_lines_tax_values_dict = compute_invoice_lines_tax_values_dict_from_tax_details(invoice_lines)

        grouping_key_generator = grouping_key_generator or default_grouping_key_generator

        # Apply 'filter_to_apply'.

        if self.move_type in ('out_refund', 'in_refund'):
            tax_rep_lines_field = 'refund_repartition_line_ids'
        else:
            tax_rep_lines_field = 'invoice_repartition_line_ids'

        filtered_invoice_lines_tax_values_dict = {}
        for invoice_line in invoice_lines:
            tax_values_list = invoice_lines_tax_values_dict.get(invoice_line, [])
            filtered_invoice_lines_tax_values_dict[invoice_line] = []

            # Search for unhandled taxes.
            taxes_set = set(invoice_line.tax_ids.flatten_taxes_hierarchy())
            for tax_values in tax_values_list:
                taxes_set.discard(tax_values['tax_id'])

                if not filter_to_apply or filter_to_apply(tax_values):
                    filtered_invoice_lines_tax_values_dict[invoice_line].append(tax_values)

            # Restore zero-tax tax details.
            for zero_tax in taxes_set:

                affect_base_amount = 0.0
                affect_base_amount_currency = 0.0
                for tax_values in tax_values_list:
                    if zero_tax in tax_values['tax_line_id'].tax_ids:
                        affect_base_amount += tax_values['tax_amount']
                        affect_base_amount_currency += tax_values['tax_amount_currency']

                for tax_rep in zero_tax[tax_rep_lines_field].filtered(lambda x: x.repartition_type == 'tax'):
                    tax_values = {
                        'base_line_id': invoice_line,
                        'tax_line_id': self.env['account.move.line'],
                        'src_line_id': invoice_line,
                        'tax_id': zero_tax,
                        'src_tax_id': zero_tax,
                        'tax_repartition_line_id': tax_rep,
                        'base_amount': invoice_line.balance + affect_base_amount,
                        'tax_amount': 0.0,
                        'base_amount_currency': invoice_line.amount_currency + affect_base_amount_currency,
                        'tax_amount_currency': 0.0,
                    }

                    if not filter_to_apply or filter_to_apply(tax_values):
                        filtered_invoice_lines_tax_values_dict[invoice_line].append(tax_values)

        # Initialize the results dict.

        invoice_global_tax_details = {
            'base_amount': 0.0,
            'tax_amount': 0.0,
            'base_amount_currency': 0.0,
            'tax_amount_currency': 0.0,
            'tax_details': defaultdict(lambda: {
                'base_amount': 0.0,
                'tax_amount': 0.0,
                'base_amount_currency': 0.0,
                'tax_amount_currency': 0.0,
                'group_tax_details': [],
            }),
            'invoice_line_tax_details': defaultdict(lambda: {
                'base_amount': 0.0,
                'tax_amount': 0.0,
                'base_amount_currency': 0.0,
                'tax_amount_currency': 0.0,
                'tax_details': defaultdict(lambda: {
                    'base_amount': 0.0,
                    'tax_amount': 0.0,
                    'base_amount_currency': 0.0,
                    'tax_amount_currency': 0.0,
                    'group_tax_details': [],
                }),
            }),
        }

        # Apply 'grouping_key_generator' to 'invoice_lines_tax_values_list' and add all values to the final results.

        for invoice_line in invoice_lines:
            tax_values_list = filtered_invoice_lines_tax_values_dict[invoice_line]

            key_by_tax = {}

            # Add to invoice global tax amounts.
            invoice_global_tax_details['base_amount'] += invoice_line.balance
            invoice_global_tax_details['base_amount_currency'] += invoice_line.amount_currency

            for tax_values in tax_values_list:
                grouping_key = grouping_key_generator(tax_values)
                serialized_grouping_key = frozendict(grouping_key)
                key_by_tax[tax_values['tax_id']] = serialized_grouping_key

                # Add to invoice line global tax amounts.
                if serialized_grouping_key not in invoice_global_tax_details['invoice_line_tax_details'][invoice_line]:
                    invoice_line_global_tax_details = invoice_global_tax_details['invoice_line_tax_details'][invoice_line]
                    invoice_line_global_tax_details.update({
                        'base_amount': invoice_line.balance,
                        'base_amount_currency': invoice_line.amount_currency,
                    })
                else:
                    invoice_line_global_tax_details = invoice_global_tax_details['invoice_line_tax_details'][invoice_line]

                self._add_edi_tax_values(invoice_global_tax_details, grouping_key, serialized_grouping_key, tax_values,
                                         key_by_tax=key_by_tax if compute_mode == 'tax_details' else None)
                self._add_edi_tax_values(invoice_line_global_tax_details, grouping_key, serialized_grouping_key, tax_values,
                                         key_by_tax=key_by_tax if compute_mode == 'tax_details' else None)

        return invoice_global_tax_details

    def _prepare_edi_vals_to_export(self):
        ''' The purpose of this helper is to prepare values in order to export an invoice through the EDI system.
        This includes the computation of the tax details for each invoice line that could be very difficult to
        handle regarding the computation of the base amount.

        :return: A python dict containing default pre-processed values.
        '''
        self.ensure_one()

        res = {
            'record': self,
            'balance_multiplicator': -1 if self.is_inbound() else 1,
            'invoice_line_vals_list': [],
        }

        # Invoice lines details.
        for index, line in enumerate(self.invoice_line_ids.filtered(lambda line: not line.display_type), start=1):
            line_vals = line._prepare_edi_vals_to_export()
            line_vals['index'] = index
            res['invoice_line_vals_list'].append(line_vals)

        # Totals.
        res.update({
            'total_price_subtotal_before_discount': sum(x['price_subtotal_before_discount'] for x in res['invoice_line_vals_list']),
            'total_price_discount': sum(x['price_discount'] for x in res['invoice_line_vals_list']),
        })

        return res

    def _update_payments_edi_documents(self):
        ''' Update the edi documents linked to the current journal entries. These journal entries must be linked to an
        account.payment of an account.bank.statement.line. This additional method is needed because the payment flow is
        not the same as the invoice one. Indeed, the edi documents must be updated when the reconciliation with some
        invoices is changing.
        '''
        edi_document_vals_list = []
        for payment in self:
            edi_formats = payment._get_reconciled_invoices().journal_id.edi_format_ids + payment.edi_document_ids.edi_format_id
            edi_formats = self.env['account.edi.format'].browse(edi_formats.ids) # Avoid duplicates
            for edi_format in edi_formats:
                existing_edi_document = payment.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)

                if edi_format._is_required_for_payment(payment):
                    if existing_edi_document:
                        existing_edi_document.write({
                            'state': 'to_send',
                            'error': False,
                            'blocking_level': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': payment.id,
                            'state': 'to_send',
                        })
                elif existing_edi_document:
                    existing_edi_document.write({
                        'state': False,
                        'error': False,
                        'blocking_level': False,
                    })

        self.env['account.edi.document'].create(edi_document_vals_list)
        self.edi_document_ids._process_documents_no_web_services()

    def _is_ready_to_be_sent(self):
        # OVERRIDE
        # Prevent a mail to be sent to the customer if the EDI document is not sent.
        self.ensure_one()
        # res = super()._is_ready_to_be_sent()

        # if not res:
        #     return False

        edi_documents_to_send = self.edi_document_ids.filtered(lambda x: x.state == 'to_send')
        return not bool(edi_documents_to_send)

    def _post(self, soft=True):
        # OVERRIDE
        # Set the electronic document to be posted and post immediately for synchronous formats.
        posted = super()._post(soft=soft)

        edi_document_vals_list = []
        for move in posted:
            for edi_format in move.journal_id.edi_format_ids:
                is_edi_needed = move.is_invoice(include_receipts=False) and edi_format._is_required_for_invoice(move)

                if is_edi_needed:
                    errors = edi_format._check_move_configuration(move)
                    if errors:
                        raise UserError(_("Invalid invoice configuration:\n\n%s") % '\n'.join(errors))

                    existing_edi_document = move.edi_document_ids.filtered(lambda x: x.edi_format_id == edi_format)
                    if existing_edi_document:
                        existing_edi_document.write({
                            'state': 'to_send',
                            'attachment_id': False,
                        })
                    else:
                        edi_document_vals_list.append({
                            'edi_format_id': edi_format.id,
                            'move_id': move.id,
                            'state': 'to_send',
                        })

        self.env['account.edi.document'].create(edi_document_vals_list)
        posted.edi_document_ids._process_documents_no_web_services()
        self.env.ref('exp_account_edi.ir_cron_edi_network')._trigger()
        return posted


        return posted

    def button_cancel(self):
        # OVERRIDE
        # Set the electronic document to be canceled and cancel immediately for synchronous formats.
        res = super().button_cancel()

        self.edi_document_ids.filtered(lambda doc: doc.state != 'sent').write({'state': 'cancelled', 'error': False, 'blocking_level': False})
        self.edi_document_ids.filtered(lambda doc: doc.state == 'sent').write({'state': 'to_cancel', 'error': False, 'blocking_level': False})
        self.edi_document_ids._process_documents_no_web_services()
        self.env.ref('exp_account_edi.ir_cron_edi_network')._trigger()

        return res

    def button_draft(self):
        # OVERRIDE
        for move in self:
            if move.edi_show_cancel_button:
                raise UserError(_(
                    "You can't edit the following journal entry %s because an electronic document has already been "
                    "sent. Please use the 'Request EDI Cancellation' button instead."
                ) % move.display_name)

        res = super().button_draft()

        self.edi_document_ids.write({'error': False, 'blocking_level': False})

        return res

    def button_cancel_posted_moves(self):
        '''Mark the edi.document related to this move to be canceled.
        '''
        to_cancel_documents = self.env['account.edi.document']
        for move in self:
            move._check_fiscalyear_lock_date()
            is_move_marked = False
            for doc in move.edi_document_ids:
                if doc.edi_format_id._needs_web_services() \
                        and doc.attachment_id \
                        and doc.state == 'sent' \
                        and move.is_invoice(include_receipts=True) \
                        and doc.edi_format_id._is_required_for_invoice(move):
                    to_cancel_documents |= doc
                    is_move_marked = True
            if is_move_marked:
                move.message_post(body=_("A cancellation of the EDI has been requested."))

        to_cancel_documents.write({'state': 'to_cancel', 'error': False, 'blocking_level': False})

    def button_abandon_cancel_posted_posted_moves(self):
        '''Cancel the request for cancellation of the EDI.
        '''
        documents = self.env['account.edi.document']
        for move in self:
            is_move_marked = False
            for doc in move.edi_document_ids:
                if doc.state == 'to_cancel' \
                        and move.is_invoice(include_receipts=True) \
                        and doc.edi_format_id._is_required_for_invoice(move):
                    documents |= doc
                    is_move_marked = True
            if is_move_marked:
                move.message_post(body=_("A request for cancellation of the EDI has been called off."))

        documents.write({'state': 'sent'})

    def _get_edi_document(self, edi_format):
        return self.edi_document_ids.filtered(lambda d: d.edi_format_id == edi_format)

    def _get_edi_attachment(self, edi_format):
        return self._get_edi_document(edi_format).attachment_id

    ####################################################
    # Import Electronic Document
    ####################################################

    def _get_create_invoice_from_attachment_decoders(self):
        # OVERRIDE
        res = super()._get_create_invoice_from_attachment_decoders()
        res.append((10, self.env['account.edi.format'].search([])._create_invoice_from_attachment))
        return res

    def _get_update_invoice_from_attachment_decoders(self, invoice):
        # OVERRIDE
        res = super()._get_update_invoice_from_attachment_decoders(invoice)
        res.append((10, self.env['account.edi.format'].search([])._update_invoice_from_attachment))
        return res

    ####################################################
    # Business operations
    ####################################################

    def button_process_edi_web_services(self):
        self.action_process_edi_web_services(with_commit=False)

    def action_process_edi_web_services(self, with_commit=True):
        docs = self.edi_document_ids.filtered(lambda d: d.state in ('to_send', 'to_cancel') and d.blocking_level != 'error')
        docs._process_documents_web_services(with_commit=with_commit)

    def _retry_edi_documents_error_hook(self):
        ''' Hook called when edi_documents are retried. For example, when it's needed to clean a field.
        TO OVERRIDE
        '''
        return

    def action_retry_edi_documents_error(self):
        self._retry_edi_documents_error_hook()
        self.edi_document_ids.write({'error': False, 'blocking_level': False})
        self.action_process_edi_web_services()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    group_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string="Originator Group of Taxes",
        index=True,
        help="The group of taxes that generated this tax line",
    )
    ####################################################
    # Export Electronic Document
    ####################################################
    @api.model
    def _get_query_tax_details_from_domain(self, domain, fallback=True):
        """ Create the tax details sub-query based on the orm domain passed as parameter.

        :param domain:      An orm domain on account.move.line.
        :param fallback:    Fallback on an approximated mapping if the mapping failed.
        :return:            A tuple <query, params>.
        """
        self.env['account.move.line'].check_access_rights('read')

        query = self.env['account.move.line']._where_calc(domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)

        tables, where_clause, where_params = query.get_sql()
        return self._get_query_tax_details(tables, where_clause, where_params, fallback=fallback)

    @api.model
    def _get_query_tax_details(self, tables, where_clause, where_params, fallback=True):
        """ Create the tax details sub-query based on the orm domain passed as parameter.

        :param tables:          The 'tables' query to inject after the FROM.
        :param where_clause:    The 'where_clause' query computed based on an orm domain.
        :param where_params:    The params to fill the 'where_clause' query.
        :param fallback:        Fallback on an approximated mapping if the mapping failed.
        :return:                A tuple <query, params>.
        """
        group_taxes = self.env['account.tax'].search([('amount_type', '=', 'group')])

        group_taxes_query_list = []
        group_taxes_params = []
        for group_tax in group_taxes:
            children_taxes = group_tax.children_tax_ids
            if not children_taxes:
                continue

            children_taxes_in_query = ','.join('%s' for dummy in children_taxes)
            group_taxes_query_list.append(f'WHEN tax.id = %s THEN ARRAY[{children_taxes_in_query}]')
            group_taxes_params.append(group_tax.id)
            group_taxes_params.extend(children_taxes.ids)

        if group_taxes_query_list:
            group_taxes_query = f'''UNNEST(CASE {' '.join(group_taxes_query_list)} ELSE ARRAY[tax.id] END)'''
        else:
            group_taxes_query = 'tax.id'

        if fallback:
            fallback_query = f'''
                UNION ALL

                SELECT
                    account_move_line.id AS tax_line_id,
                    base_line.id AS base_line_id,
                    base_line.id AS src_line_id,
                    base_line.balance AS base_amount,
                    base_line.amount_currency AS base_amount_currency
                FROM {tables}
                LEFT JOIN base_tax_line_mapping ON
                    base_tax_line_mapping.tax_line_id = account_move_line.id
                JOIN account_move_line_account_tax_rel tax_rel ON
                    tax_rel.account_tax_id = COALESCE(account_move_line.group_tax_id, account_move_line.tax_line_id)
                JOIN account_move_line base_line ON
                    base_line.id = tax_rel.account_move_line_id
                    AND base_line.tax_repartition_line_id IS NULL
                    AND base_line.move_id = account_move_line.move_id
                    AND base_line.currency_id = account_move_line.currency_id
                WHERE base_tax_line_mapping.tax_line_id IS NULL
                AND {where_clause}
            '''
            fallback_params = where_params
        else:
            fallback_query = ''
            fallback_params = []

        return f'''
            /*
            As example to explain the different parts of the query, we'll consider a move with the following lines:
            Name            Tax_line_id         Tax_ids                 Debit       Credit      Base lines
            ---------------------------------------------------------------------------------------------------
            base_line_1                         10_affect_base, 20      1000
            base_line_2                         10_affect_base, 5       2000
            base_line_3                         10_affect_base, 5       3000
            tax_line_1      10_affect_base      20                                  100         base_line_1
            tax_line_2      20                                                      220         base_line_1
            tax_line_3      10_affect_base      5                                   500         base_line_2/3
            tax_line_4      5                                                       275         base_line_2/3
            */

            WITH affecting_base_tax_ids AS (

                /*
                This CTE builds a reference table based on the tax_ids field, with the following changes:
                  - flatten the group of taxes
                  - exclude the taxes having 'is_base_affected' set to False.
                Those allow to match only base_line_1 when finding the base lines of tax_line_1, as we need to find
                base lines having a 'affecting_base_tax_ids' ending with [10_affect_base, 20], not only containing
                '10_affect_base'. Otherwise, base_line_2/3 would also be matched.
                In our example, as all the taxes are set to be affected by previous ones affecting the base, the
                result is similar to the table 'account_move_line_account_tax_rel':
                Id                 Tax_ids
                -------------------------------------------
                base_line_1        [10_affect_base, 20]
                base_line_2        [10_affect_base, 5]
                base_line_3        [10_affect_base, 5]
                */

                SELECT
                    sub.line_id AS id,
                    ARRAY_AGG(sub.tax_id ORDER BY sub.sequence, sub.tax_id) AS tax_ids
                FROM (
                    SELECT
                        tax_rel.account_move_line_id AS line_id,
                        {group_taxes_query} AS tax_id,
                        tax.sequence
                    FROM {tables}
                    JOIN account_move_line_account_tax_rel tax_rel ON account_move_line.id = tax_rel.account_move_line_id
                    JOIN account_tax tax ON tax.id = tax_rel.account_tax_id
                    WHERE tax.is_base_affected
                    AND {where_clause}
                ) AS sub
                GROUP BY sub.line_id
            ),

            base_tax_line_mapping AS (

                /*
                Create the mapping of each tax lines with their corresponding base lines.

                In the example, it will give the following values:
                    base_line_id     tax_line_id    base_amount
                    -------------------------------------------
                    base_line_1      tax_line_1         1000
                    base_line_1      tax_line_2         1000
                    base_line_2      tax_line_3         2000
                    base_line_2      tax_line_4         2000
                    base_line_3      tax_line_3         3000
                    base_line_3      tax_line_4         3000
                */

                SELECT
                    account_move_line.id AS tax_line_id,
                    base_line.id AS base_line_id,
                    base_line.balance AS base_amount,
                    base_line.amount_currency AS base_amount_currency

                FROM {tables}
                JOIN account_tax_repartition_line tax_rep ON
                    tax_rep.id = account_move_line.tax_repartition_line_id
                JOIN account_tax tax ON
                    tax.id = account_move_line.tax_line_id
                JOIN res_currency curr ON
                    curr.id = account_move_line.currency_id
                JOIN res_currency comp_curr ON
                    comp_curr.id = account_move_line.company_currency_id
                JOIN account_move_line_account_tax_rel tax_rel ON
                    tax_rel.account_tax_id = COALESCE(account_move_line.group_tax_id, account_move_line.tax_line_id)
                JOIN account_move move ON
                    move.id = account_move_line.move_id
                JOIN account_move_line base_line ON
                    base_line.id = tax_rel.account_move_line_id
                    AND base_line.tax_repartition_line_id IS NULL
                    AND base_line.move_id = account_move_line.move_id
                    AND (
                        move.move_type != 'entry'
                        OR
                        sign(account_move_line.balance) = sign(base_line.balance * tax.amount * tax_rep.factor_percent)
                    )
                    AND COALESCE(base_line.partner_id, 0) = COALESCE(account_move_line.partner_id, 0)
                    AND base_line.currency_id = account_move_line.currency_id
                    AND (
                        COALESCE(tax_rep.account_id, base_line.account_id) = account_move_line.account_id
                        OR (tax.tax_exigibility = 'on_payment' AND tax.cash_basis_transition_account_id IS NOT NULL)
                    )
                    AND (
                        NOT tax.analytic
                        OR (base_line.analytic_account_id IS NULL AND account_move_line.analytic_account_id IS NULL)
                        OR base_line.analytic_account_id = account_move_line.analytic_account_id
                    )
                LEFT JOIN affecting_base_tax_ids tax_line_tax_ids ON tax_line_tax_ids.id = account_move_line.id
                JOIN affecting_base_tax_ids base_line_tax_ids ON base_line_tax_ids.id = base_line.id
                WHERE account_move_line.tax_repartition_line_id IS NOT NULL
                    AND {where_clause}
                    AND (
                        -- keeping only the rows from affecting_base_tax_lines that end with the same taxes applied (see comment in affecting_base_tax_ids)
                        NOT tax.include_base_amount
                        OR base_line_tax_ids.tax_ids[ARRAY_LENGTH(base_line_tax_ids.tax_ids, 1) - COALESCE(ARRAY_LENGTH(tax_line_tax_ids.tax_ids, 1), 0):ARRAY_LENGTH(base_line_tax_ids.tax_ids, 1)]
                            = ARRAY[account_move_line.tax_line_id] || COALESCE(tax_line_tax_ids.tax_ids, ARRAY[]::INTEGER[])
                    )
            ),


            tax_amount_affecting_base_to_dispatch AS (

                /*
                Computes the total amount to dispatch in case of tax lines affecting the base of subsequent taxes.
                Such tax lines are an additional base amount for others lines, that will be truly dispatch in next
                CTE.

                In the example:
                    - tax_line_1 is an additional base of 100.0 from base_line_1 for tax_line_2.
                    - tax_line_3 is an additional base of 2/5 * 500.0 = 200.0 from base_line_2 for tax_line_4.
                    - tax_line_3 is an additional base of 3/5 * 500.0 = 300.0 from base_line_3 for tax_line_4.

                    src_line_id    base_line_id     tax_line_id    total_base_amount
                    -------------------------------------------------------------
                    tax_line_1     base_line_1      tax_line_2         1000
                    tax_line_3     base_line_2      tax_line_4         5000
                    tax_line_3     base_line_3      tax_line_4         5000
                */

                SELECT
                    tax_line.id AS tax_line_id,
                    base_line.id AS base_line_id,
                    account_move_line.id AS src_line_id,

                    tax_line.company_id,
                    comp_curr.id AS company_currency_id,
                    comp_curr.decimal_places AS comp_curr_prec,
                    curr.id AS currency_id,
                    curr.decimal_places AS curr_prec,

                    tax_line.tax_line_id AS tax_id,

                    base_line.balance AS base_amount,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.balance < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE base_line.balance
                        END
                    ) OVER (PARTITION BY tax_line.id, account_move_line.id ORDER BY tax_line.tax_line_id, base_line.id) AS cumulated_base_amount,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.balance < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE base_line.balance
                        END
                    ) OVER (PARTITION BY tax_line.id, account_move_line.id) AS total_base_amount,
                    account_move_line.balance AS total_tax_amount,

                    base_line.amount_currency AS base_amount_currency,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.amount_currency < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE base_line.amount_currency
                        END
                    ) OVER (PARTITION BY tax_line.id, account_move_line.id ORDER BY tax_line.tax_line_id, base_line.id) AS cumulated_base_amount_currency,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.amount_currency < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE base_line.amount_currency
                        END
                    ) OVER (PARTITION BY tax_line.id, account_move_line.id) AS total_base_amount_currency,
                    account_move_line.amount_currency AS total_tax_amount_currency

                FROM {tables}
                JOIN account_tax tax_include_base_amount ON
                    tax_include_base_amount.include_base_amount
                    AND tax_include_base_amount.id = account_move_line.tax_line_id
                JOIN base_tax_line_mapping base_tax_line_mapping ON
                    base_tax_line_mapping.tax_line_id = account_move_line.id
                JOIN account_move_line_account_tax_rel tax_rel ON
                    tax_rel.account_move_line_id = base_tax_line_mapping.tax_line_id
                JOIN account_tax tax ON
                    tax.id = tax_rel.account_tax_id
                JOIN base_tax_line_mapping tax_line_matching ON
                    tax_line_matching.base_line_id = base_tax_line_mapping.base_line_id
                JOIN account_move_line tax_line ON
                    tax_line.id = tax_line_matching.tax_line_id
                    AND tax_line.tax_line_id = tax_rel.account_tax_id
                JOIN res_currency curr ON
                    curr.id = tax_line.currency_id
                JOIN res_currency comp_curr ON
                    comp_curr.id = tax_line.company_currency_id
                JOIN account_move_line base_line ON
                    base_line.id = base_tax_line_mapping.base_line_id
                WHERE {where_clause}
            ),


            base_tax_matching_base_amounts AS (

                /*
                Build here the full mapping tax lines <=> base lines containing the final base amounts.
                This is done in a 3-parts union.

                Note: src_line_id is used only to build a unique ID.
                */

                /*
                PART 1: raw mapping computed in base_tax_line_mapping.
                */

                SELECT
                    tax_line_id,
                    base_line_id,
                    base_line_id AS src_line_id,
                    base_amount,
                    base_amount_currency
                FROM base_tax_line_mapping

                UNION ALL

                /*
                PART 2: Dispatch the tax amount of tax lines affecting the base of subsequent ones, using
                tax_amount_affecting_base_to_dispatch.

                This will effectively add the following rows:
                base_line_id    tax_line_id     src_line_id     base_amount
                -------------------------------------------------------------
                base_line_1     tax_line_2      tax_line_1      100
                base_line_2     tax_line_4      tax_line_3      200
                base_line_3     tax_line_4      tax_line_3      300
                */

                SELECT
                    sub.tax_line_id,
                    sub.base_line_id,
                    sub.src_line_id,

                    ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount) * sub.total_tax_amount * ABS(sub.cumulated_base_amount) / NULLIF(sub.total_base_amount, 0.0), 0.0),
                        sub.comp_curr_prec
                    )
                    - LAG(ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount) * sub.total_tax_amount * ABS(sub.cumulated_base_amount) / NULLIF(sub.total_base_amount, 0.0), 0.0),
                        sub.comp_curr_prec
                    ), 1, 0.0)
                    OVER (
                        PARTITION BY sub.tax_line_id, sub.src_line_id ORDER BY sub.tax_id, sub.base_line_id
                    ) AS base_amount,

                    ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount_currency) * sub.total_tax_amount_currency * ABS(sub.cumulated_base_amount_currency) / NULLIF(sub.total_base_amount_currency, 0.0), 0.0),
                        sub.curr_prec
                    )
                    - LAG(ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount_currency) * sub.total_tax_amount_currency * ABS(sub.cumulated_base_amount_currency) / NULLIF(sub.total_base_amount_currency, 0.0), 0.0),
                        sub.curr_prec
                    ), 1, 0.0)
                    OVER (
                        PARTITION BY sub.tax_line_id, sub.src_line_id ORDER BY sub.tax_id, sub.base_line_id
                    ) AS base_amount_currency
                FROM tax_amount_affecting_base_to_dispatch sub
                JOIN account_move_line tax_line ON
                    tax_line.id = sub.tax_line_id

                /*
                PART 3: In case of the matching failed because the configuration changed or some journal entries
                have been imported, construct a simple mapping as a fallback. This mapping is super naive and only
                build based on the 'tax_ids' and 'tax_line_id' fields, nothing else. Hence, the mapping will not be
                exact but will give an acceptable approximation.

                Skipped if the 'fallback' method parameter is False.
                */
                {fallback_query}
            ),


            base_tax_matching_all_amounts AS (

                /*
                Complete base_tax_matching_base_amounts with the tax amounts (prorata):
                base_line_id    tax_line_id     src_line_id     base_amount     tax_amount
                --------------------------------------------------------------------------
                base_line_1     tax_line_1      base_line_1     1000            100
                base_line_1     tax_line_2      base_line_1     1000            (1000 / 1100) * 220 = 200
                base_line_1     tax_line_2      tax_line_1      100             (100 / 1100) * 220 = 20
                base_line_2     tax_line_3      base_line_2     2000            (2000 / 5000) * 500 = 200
                base_line_2     tax_line_4      base_line_2     2000            (2000 / 5500) * 275 = 100
                base_line_2     tax_line_4      tax_line_3      200             (200 / 5500) * 275 = 10
                base_line_3     tax_line_3      base_line_3     3000            (3000 / 5000) * 500 = 300
                base_line_3     tax_line_4      base_line_3     3000            (3000 / 5500) * 275 = 150
                base_line_3     tax_line_4      tax_line_3      300             (300 / 5500) * 275 = 15
                */

                SELECT
                    sub.tax_line_id,
                    sub.base_line_id,
                    sub.src_line_id,

                    tax_line.tax_line_id AS tax_id,
                    tax_line.group_tax_id,
                    tax_line.tax_repartition_line_id,

                    tax_line.company_id,
                    comp_curr.id AS company_currency_id,
                    comp_curr.decimal_places AS comp_curr_prec,
                    curr.id AS currency_id,
                    curr.decimal_places AS curr_prec,
                    (
                        tax.tax_exigibility != 'on_payment'
                        OR tax_move.tax_cash_basis_rec_id IS NOT NULL
                        OR tax_move.always_tax_exigible
                    ) AS tax_exigible,
                    base_line.account_id AS base_account_id,

                    sub.base_amount,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.balance < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE sub.base_amount
                        END
                    ) OVER (PARTITION BY tax_line.id ORDER BY tax_line.tax_line_id, sub.base_line_id, sub.src_line_id) AS cumulated_base_amount,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.balance < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE sub.base_amount
                        END
                    ) OVER (PARTITION BY tax_line.id) AS total_base_amount,
                    tax_line.balance AS total_tax_amount,

                    sub.base_amount_currency,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.amount_currency < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE sub.base_amount_currency
                        END
                    ) OVER (PARTITION BY tax_line.id ORDER BY tax_line.tax_line_id, sub.base_line_id, sub.src_line_id) AS cumulated_base_amount_currency,
                    SUM(
                        CASE WHEN tax.amount_type = 'fixed'
                        THEN CASE WHEN base_line.amount_currency < 0 THEN -1 ELSE 1 END * ABS(COALESCE(base_line.quantity, 1.0))
                        ELSE sub.base_amount_currency
                        END
                    ) OVER (PARTITION BY tax_line.id) AS total_base_amount_currency,
                    tax_line.amount_currency AS total_tax_amount_currency

                FROM base_tax_matching_base_amounts sub
                JOIN account_move_line tax_line ON
                    tax_line.id = sub.tax_line_id
                JOIN account_move tax_move ON
                    tax_move.id = tax_line.move_id
                JOIN account_move_line base_line ON
                    base_line.id = sub.base_line_id
                JOIN account_tax tax ON
                    tax.id = tax_line.tax_line_id
                JOIN res_currency curr ON
                    curr.id = tax_line.currency_id
                JOIN res_currency comp_curr ON
                    comp_curr.id = tax_line.company_currency_id

            )


           /* Final select that makes sure to deal with rounding errors, using LAG to dispatch the last cents. */

            SELECT
                sub.tax_line_id || '-' || sub.base_line_id || '-' || sub.src_line_id AS id,

                sub.base_line_id,
                sub.tax_line_id,
                sub.src_line_id,

                sub.tax_id,
                sub.group_tax_id,
                sub.tax_exigible,
                sub.base_account_id,
                sub.tax_repartition_line_id,

                sub.base_amount,
                COALESCE(
                    ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount) * sub.total_tax_amount * ABS(sub.cumulated_base_amount) / NULLIF(sub.total_base_amount, 0.0), 0.0),
                        sub.comp_curr_prec
                    )
                    - LAG(ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount) * sub.total_tax_amount * ABS(sub.cumulated_base_amount) / NULLIF(sub.total_base_amount, 0.0), 0.0),
                        sub.comp_curr_prec
                    ), 1, 0.0)
                    OVER (
                        PARTITION BY sub.tax_line_id ORDER BY sub.tax_id, sub.base_line_id
                    ),
                    0.0
                ) AS tax_amount,

                sub.base_amount_currency,
                COALESCE(
                    ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount_currency) * sub.total_tax_amount_currency * ABS(sub.cumulated_base_amount_currency) / NULLIF(sub.total_base_amount_currency, 0.0), 0.0),
                        sub.curr_prec
                    )
                    - LAG(ROUND(
                        COALESCE(SIGN(sub.cumulated_base_amount_currency) * sub.total_tax_amount_currency * ABS(sub.cumulated_base_amount_currency) / NULLIF(sub.total_base_amount_currency, 0.0), 0.0),
                        sub.curr_prec
                    ), 1, 0.0)
                    OVER (
                        PARTITION BY sub.tax_line_id ORDER BY sub.tax_id, sub.base_line_id
                    ),
                    0.0
                ) AS tax_amount_currency
            FROM base_tax_matching_all_amounts sub
        ''', group_taxes_params + where_params + where_params + where_params + fallback_params

    def _prepare_edi_vals_to_export(self):
        ''' The purpose of this helper is the same as '_prepare_edi_vals_to_export' but for a single invoice line.
        This includes the computation of the tax details for each invoice line or the management of the discount.
        Indeed, in some EDI, we need to provide extra values depending the discount such as:
        - the discount as an amount instead of a percentage.
        - the price_unit but after subtraction of the discount.

        :return: A python dict containing default pre-processed values.
        '''
        self.ensure_one()

        if self.discount == 100.0:
            gross_price_subtotal = self.currency_id.round(self.price_unit * self.quantity)
        else:
            gross_price_subtotal = self.currency_id.round(self.price_subtotal / (1 - self.discount / 100.0))

        res = {
            'line': self,
            'price_unit_after_discount': self.currency_id.round(self.price_unit * (1 - (self.discount / 100.0))),
            'price_subtotal_before_discount': gross_price_subtotal,
            'price_subtotal_unit': self.currency_id.round(self.price_subtotal / self.quantity) if self.quantity else 0.0,
            'price_total_unit': self.currency_id.round(self.price_total / self.quantity) if self.quantity else 0.0,
            'price_discount': gross_price_subtotal - self.price_subtotal,
            'price_discount_unit': (gross_price_subtotal - self.price_subtotal) / self.quantity if self.quantity else 0.0,
            'gross_price_total_unit': self.currency_id.round(gross_price_subtotal / self.quantity) if self.quantity else 0.0,
            'unece_uom_code': self.product_id.product_tmpl_id.uom_id._get_unece_code(),
        }
        return res

    def reconcile(self):
        # OVERRIDE
        # In some countries, the payments must be sent to the government under some condition. One of them could be
        # there is at least one reconciled invoice to the payment. Then, we need to update the state of the edi
        # documents during the reconciliation.
        all_lines = self + self.matched_debit_ids.debit_move_id + self.matched_credit_ids.credit_move_id
        payments = all_lines.move_id.filtered(lambda move: move.payment_id or move.statement_line_id)

        invoices_per_payment_before = {pay: pay._get_reconciled_invoices() for pay in payments}
        res = super().reconcile()
        invoices_per_payment_after = {pay: pay._get_reconciled_invoices() for pay in payments}

        changed_payments = self.env['account.move']
        for payment, invoices_after in invoices_per_payment_after.items():
            invoices_before = invoices_per_payment_before[payment]

            if set(invoices_after.ids) != set(invoices_before.ids):
                changed_payments |= payment
        changed_payments._update_payments_edi_documents()

        return res

    def remove_move_reconcile(self):
        # OVERRIDE
        # When a payment has been sent to the government, it usually contains some information about reconciled
        # invoices. If the user breaks a reconciliation, the related payments must be cancelled properly and then, a new
        # electronic document must be generated.
        all_lines = self + self.matched_debit_ids.debit_move_id + self.matched_credit_ids.credit_move_id
        payments = all_lines.move_id.filtered(lambda move: move.payment_id or move.statement_line_id)

        invoices_per_payment_before = {pay: pay._get_reconciled_invoices() for pay in payments}
        res = super().remove_move_reconcile()
        invoices_per_payment_after = {pay: pay._get_reconciled_invoices() for pay in payments}

        changed_payments = self.env['account.move']
        for payment, invoices_after in invoices_per_payment_after.items():
            invoices_before = invoices_per_payment_before[payment]

            if set(invoices_after.ids) != set(invoices_before.ids):
                changed_payments |= payment
        changed_payments._update_payments_edi_documents()

        return res
