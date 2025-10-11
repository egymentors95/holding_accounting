from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # TODO remove this field 'invoice_rec_id' after launching server action server_action_migrate_invoice_rec_id
    invoice_rec_id = fields.Many2one(comodel_name='account.move', string='Invoice', copy=False)
    invoice_rec_ids = fields.Many2many(comodel_name='account.move', copy=False)

    @api.model
    def migrate_invoice_rec_id_to_invoice_rec_ids(self):
        # Get all records where invoice_rec_id is set
        records = self.search([('invoice_rec_id', '!=', False)])

        for record in records:
            if record.invoice_rec_id:
                move_id = record.invoice_rec_id.id

                if isinstance(move_id, int):
                    record.write({
                        'invoice_rec_id': False,
                        'invoice_rec_ids': [(4, move_id)]
                    })

        print(f">>> Migration completed for {len(records)} records <<<")


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            # invoice_payment = self.env['account.payment'].search(
            #     [('invoice_rec_id', '=', active_id),
            #      ('state', '=', 'draft')])
            invoice_payment = self.env['account.payment'].search([('state', '=', 'draft')]).filtered(
                lambda r: set(active_ids) & set(r.invoice_rec_ids.ids))
            if invoice_payment:
                raise UserError(
                    _('You can not create payment for this invoice because there is a draft payment for it'))

        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        process_final = [item for item in to_process if item['create_vals']['payment_type'] != 'outbound']
        self._post_payments(process_final, edit_mode=edit_mode)
        self._reconcile_payments(process_final, edit_mode=edit_mode)
        for payment in payments:
            if payment.payment_type == 'outbound':
                payment.invoice_rec_ids = [(4, active_id) for active_id in active_ids]
                payment.action_cancel()
                payment.action_draft()
                for line in payment.move_id.line_ids:
                    if payment.is_internal_transfer:
                        if payment.payment_type == 'outbound':
                            liquidity_line_name = _('Transfer from %s', payment.journal_id.name)
                        else:
                            liquidity_line_name = _('Transfer to %s', payment.journal_id.name)
                    else:
                        liquidity_line_name = payment.payment_reference
                    payment_display_name = payment._prepare_payment_display_name()
                    default_line_name = self._get_payment_line_name(
                        _("Internal Transfer") if payment.is_internal_transfer else payment_display_name[
                            '%s-%s' % (payment.payment_type, payment.partner_type)],
                        payment.amount,
                        payment.currency_id,
                        payment.date,
                        partner_or_name=payment.invoice_purpose or payment.partner_id,
                    )
                    if line.account_id.id in [payment.destination_account_id.id]:
                        line.name = liquidity_line_name or default_line_name
        return payments

    def _get_payment_line_name(self, document, amount, currency, date, partner_or_name=None):
        '''Custom function to create name for payment lines'''
        # Start with standard format similar to _get_default_line_name
        values = ['%s %s' % (document, formatLang(self.env, amount, currency_obj=currency))]

        if partner_or_name:
            if hasattr(partner_or_name, 'display_name'):
                values.append(partner_or_name.display_name)
            else:
                values.append(str(partner_or_name))

        values.append(format_date(self.env, fields.Date.to_string(date)))
        return ' - '.join(values)
