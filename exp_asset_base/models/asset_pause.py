# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class AssetPause(models.Model):
    _name = 'asset.pause'
    _description = 'Pause Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'asset_id'

    date = fields.Date(string='Pause date', required=True, default=fields.Date.today(),tracking=True)
    asset_id = fields.Many2one('account.asset', domain="[('asset_type', '=', 'purchase'), ('state', '!=', 'model'), ('parent_id', '=', False)]",required=True,tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'),('confirm', 'Confirmed'),('approve', 'Approved'),('done', 'Done')],default='draft',readonly=True,tracking=True)

    def act_confirm(self):
        self.state = 'confirm'

    def act_approve(self):
        self.state = 'approve'

    def act_draft(self):
        self.state = 'draft'

    def do_action(self):
        for record in self:
            record.asset_id.pause(pause_date=record.date)
        return self.write({'state':'done'})
