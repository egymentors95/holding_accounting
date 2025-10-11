# -*- coding: utf-8 -*-
# © Copyright (C) 2021 Expert Co. Ltd(<http:/www.exp-sa.com>)

from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    custody_type = fields.Selection(
        selection=[('personal', 'Personal'), ('general', 'General')],
    )
    custody_period = fields.Selection(
        selection=[('temporary', 'Temporary'), ('permanent', 'Permanent')],
    )
    purpose = fields.Html()
    return_date = fields.Date()
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Current Department'
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Current Employee'
    )
    status = fields.Selection(
        selection_add=[('reserved', 'Reserved'), ('assigned', 'Assigned'), ('scrap', 'Scrap')]
    )
    asset_operation_count = fields.Integer(
        compute='_asset_operation_count',
        string='# Done Operations',
        help="Number of done asset operations"
    )

    def _asset_operation_count(self):
        for asset in self:
            asset.asset_operation_count = len(
                self.env['account.asset.operation'].search([('asset_id', '=', asset.id), ('state', '=', 'done')]))

    def open_asset_operation(self):
        return {
            'name': _('Asset Operations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.operation',
            'type': 'ir.actions.act_window',
            'domain': [('asset_id', '=', self.id)],
            'view_id': self.env.ref('exp_asset_custody.view_account_asset_operation_tree').id,
            'views': [(self.env.ref('exp_asset_custody.view_account_asset_operation_tree').id, 'tree'),
                      (self.env.ref('exp_asset_custody.view_account_asset_operation_form').id, 'form')],
            'context': {'active_model': False, 'search_default_done': True},
            'flags': {'search_view': True, 'action_buttons': False},
        }

    @api.model
    def _asset_cron(self):
        super(AccountAssetAsset, self)._asset_cron()
        today = fields.Date.today()
        for asset in self.search([('return_date', '=', today)]):
            self.env['mail.activity'].sudo().create({
                'res_model_id': self.env.ref('account_asset.model_account_asset_asset').id,
                'res_id': asset.id,
                'user_id': asset.responsible_user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('The period of %s is finished %s.') % (asset.name, asset.return_date),
                'date_deadline': asset.return_date,
            })
