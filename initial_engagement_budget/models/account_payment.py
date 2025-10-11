from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    invoice_purpose = fields.Char(string='Purpose', compute='_compute_invoice_purpose', store=True)
    has_in_invoice = fields.Boolean(compute='_compute_has_in_invoice',store=True)

    @api.depends('invoice_rec_ids.move_type')
    def _compute_has_in_invoice(self):
        for rec in self:
            rec.has_in_invoice = any(inv.move_type == 'in_invoice' for inv in rec.invoice_rec_ids)

    @api.depends('invoice_rec_ids.purpose')
    def _compute_invoice_purpose(self):
        for rec in self:
            purposes = rec.invoice_rec_ids.mapped('purpose')
            if len(purposes) > 1:
                rec.invoice_purpose = '/'.join(filter(None, purposes))
            elif len(purposes) == 1:
                rec.invoice_purpose = purposes[0]
            else:
                rec.invoice_purpose = ''
