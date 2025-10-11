from odoo import fields, models, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    destination_journal_id = fields.Many2one(comodel_name='account.journal')
    # available_account_receiving_method_ids = fields.Many2many('account.payment.method.line', compute="_compute_available_account_receiving_method_ids")
    # account_receiving_method_id = fields.Many2one(
    #     'account.payment.method.line', 
    #     string="Receiving Method",
    #     default=False
    # )
    paired_internal_transfer_payment_id = fields.Many2one('account.payment',
                                                          help="When an internal transfer is posted, a paired payment is created. "
                                                               "They are cross referenced trough this field",
                                                          copy=False)


    # @api.depends('destination_journal_id')
    # def _compute_available_account_receiving_method_ids(self):
    #     AccountPaymentMethodLine = self.env['account.payment.method.line'].sudo()
    #     for rec in self:
    #         rec.available_account_receiving_method_ids = AccountPaymentMethodLine.search([('id', 'in', self.destination_journal_id.outbound_payment_method_line_ids.ids)])

    # @api.onchange('destination_journal_id')
    # def _onchange_destination_journal_id(self):
    #     self.account_receiving_method_id = False

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if payment.is_internal_transfer:
                paired_payment = payment.copy({
                    'journal_id': payment.destination_journal_id.id,
                    'destination_journal_id': payment.journal_id.id,
                    'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                    'move_id':None,
                    'ref': payment.ref,
                    'paired_internal_transfer_payment_id': payment.id,
                    'date': payment.date,
                })
                paired_payment.move_id._post(soft=False)
                payment.paired_internal_transfer_payment_id = paired_payment

                body = _(
                    'This payment has been created from <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                           payment.id, payment.name)
                paired_payment.message_post(body=body)
                body = _(
                    'A second payment has been created: <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                           paired_payment.id, paired_payment.name)
                payment.message_post(body=body)
                paired_payment.state='posted'
                lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                    lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
                lines.reconcile()

        return res
