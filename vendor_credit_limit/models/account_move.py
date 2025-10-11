from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        result = super(AccountMove, self).action_post()
        for inv in self:
            if inv.move_type in {'out_refund', 'out_invoice'}:
                partner = inv.partner_id
                invoice_date = inv.invoice_date or fields.Date.today()

                if partner and partner.agreement_limit:
                    for lim in partner.limit_ids:
                        if lim.remaining_period == 0 :
                            raise ValidationError(_("❌ You have exceeded the allowed period."))
                        days_passed = (invoice_date - lim.create_date.date()).days
                        if days_passed <= lim.period:
                            if inv.amount_total <= lim.residual_credit:
                                lim.used_credit += inv.amount_total
                                return result
                            else:
                                raise ValidationError(_("❌ You have exceeded the allowed limit!"))

                    raise ValidationError(_("❌ No valid credit agreement found within the allowed period."))

        return result

    def button_draft(self):
        result = super(AccountMove, self).button_draft()
        for inv in self:
            if inv.move_type in {'out_refund', 'out_invoice'}:
                partner = inv.partner_id
                if partner and partner.agreement_limit:
                    for lim in partner.limit_ids:
                        days_passed = (inv.invoice_date - lim.create_date.date()).days
                        if days_passed <= lim.period:
                            lim.used_credit -= inv.amount_total
                            return result
        return result