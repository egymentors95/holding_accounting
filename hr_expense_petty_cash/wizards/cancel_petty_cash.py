# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PettyCash(models.TransientModel):
  

    _name = "petty.cash.cancel.wizard"
    _description = "petty refuse Reason wizard"

    reason = fields.Text(string='Cancel Request Reason', required=True)
    petty_id = fields.Many2one('petty.cash')
    user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)

    @api.model
    def default_get(self, fields):
        res = super(PettyCash, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
      
        res.update({'petty_id': active_ids[0] if active_ids else False})
        return res


    def request_cancel_reason(self):
        self.ensure_one()
        print('zainab')
        self.petty_id.write({'state':'running'})
        return {'type': 'ir.actions.act_window_close'}

