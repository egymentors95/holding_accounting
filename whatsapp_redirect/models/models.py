from odoo import models, fields, api, _
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    def send_msg(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Whatsapp Message'),
            'res_model': 'whatsapp.message.wizard',
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_user_id': self.partner_id.id,
                'default_invoice_id': self.id,
                'default_message': 'Dear customer, please find your invoice attached below.'
            },
        }


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def send_msg(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id,
                            'default_message': 'dear customer this is your Invoice'},
                }
