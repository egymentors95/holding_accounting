from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_purpose = fields.Char(string='Purpose', compute='_compute_payment_purpose', store=True)
    has_in_payment = fields.Boolean(compute='_compute_has_in_payment', store=True)

    @api.depends('payment_id.invoice_rec_ids')
    def _compute_has_in_payment(self):
        for rec in self:
            rec.has_in_payment = rec.payment_id and any(
                inv.move_type == 'in_invoice' for inv in rec.payment_id.invoice_rec_ids)

    @api.depends('payment_id', 'payment_id.invoice_purpose')
    def _compute_payment_purpose(self):
        for rec in self:
            if rec.payment_id:
                rec.payment_purpose = rec.payment_id.invoice_purpose
            else:
                rec.payment_purpose = False
