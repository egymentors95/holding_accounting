
from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_custody_journal = fields.Boolean(
        string="Is Custody Journal",
        compute="_compute_is_custody_journal"
    )

    custody_partner_id = fields.Many2one(
        'res.partner',
        string="Custody Partner"
    )

    @api.onchange('journal_id')
    def _compute_is_custody_journal(self):
        for rec in self:
            rec.is_custody_journal = rec.journal_id.custody_journal if rec.journal_id else False
            if not rec.is_custody_journal:
                rec.custody_partner_id = False

            return {
                'domain': {
                    'custody_partner_id': rec._get_custody_partner_domain()
                }
            }

    def _get_custody_partner_domain(self):
        """Create domain for partners based on the selected journal and positive remaining_amount"""
        if not self.journal_id or not self.is_custody_journal:
            return [('id', '=', False)]

        pledge_requests = self.env['hr.request.pledge'].search([
            ('journal_id', '=', self.journal_id.id),
            ('remaining_amount', '>', 0),
        ])

        employee_ids = pledge_requests.mapped('employee_id')

        partner_ids = []
        for employee in employee_ids:
            if employee.user_id and employee.user_id.partner_id:
                partner_ids.append(employee.user_id.partner_id.id)

        return [('id', 'in', partner_ids)] if partner_ids else [('id', '=', False)]

    @api.onchange('custody_partner_id')
    def _onchange_custody_partner_id(self):
        if self.custody_partner_id and self.journal_id:
            valid_partners = self._get_custody_partner_domain()
            if valid_partners and ('id', 'in', valid_partners[0][2]) and self.custody_partner_id.id not in \
                    valid_partners[0][2]:
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('The selected partner is not linked to any employee using this journal.')
                    }
                }

    def _create_payments(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids')
        if active_ids:
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
            if hasattr(self, 'is_custody_journal') and self.is_custody_journal \
                    and hasattr(self, 'custody_partner_id') and self.custody_partner_id:


                for line in payment.move_id.line_ids:
                    if line.credit > 0:
                        line.write({'partner_id': self.custody_partner_id.id})

        return payments

    def action_create_payments(self):
        # Call the original method to create payments
        for payment in self:
            if payment.is_custody_journal and not payment.custody_partner_id:
                raise UserError(
                    _("دفتر العهدة يتطلب تعيين شريك (custody_partner_id). الرجاء التحقق من إعدادات الدفتر."))

        payments = self._create_payments()

        # Update `move_id` values to include `takaful_sponsorship_id`
        # if self.is_refund_sponsorship:
        #     for payment in payments:
        #         if payment.move_id:  # Ensure the payment has a move_id
        #             payment.move_id.takaful_sponsorship_id = self.takaful_sponsorship_id.id

        # Prepare the action for redirection
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action