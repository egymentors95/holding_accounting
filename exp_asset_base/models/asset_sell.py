# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetSell(models.Model):
    _name = 'asset.sell'
    _description = 'Sell Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'asset_id'

    asset_id = fields.Many2one('account.asset', domain="[('asset_type', '=', 'purchase'), ('state', '!=', 'model'), ('parent_id', '=', False)]",required=True,tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    action = fields.Selection([('sell', 'Sell'), ('dispose', 'Dispose')], required=True, default='sell',tracking=True)
    invoice_id = fields.Many2one('account.move', string="Customer Invoice", help="The disposal invoice is needed in order to generate the closing journal entry.", domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]",tracking=True)
    invoice_line_id = fields.Many2one('account.move.line', help="There are multiple lines that could be the related to this asset", domain="[('move_id', '=', invoice_id), ('exclude_from_invoice_tab', '=', False)]",tracking=True)
    select_invoice_line_id = fields.Boolean(compute="_compute_select_invoice_line_id")
    gain_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('type','!=','view')]", related='company_id.gain_account_id', help="Account used to write the journal item in case of gain", readonly=False,tracking=True)
    loss_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", related='company_id.loss_account_id', help="Account used to write the journal item in case of loss", readonly=False,tracking=True)

    gain_or_loss = fields.Selection([('gain', 'Gain'), ('loss', 'Loss'), ('no', 'No')], compute='_compute_gain_or_loss', help="Technical field to know is there was a gain or a loss in the selling of the asset",tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'),('confirm', 'Confirmed'),('approve', 'Approved'),('done', 'Done')],default='draft',readonly=True,tracking=True)

    def act_confirm(self):
        self.state = 'confirm'

    def act_approve(self):
        self.state = 'approve'

    def act_draft(self):
        self.state = 'draft'

    @api.depends('invoice_id', 'action')
    def _compute_select_invoice_line_id(self):
        for record in self:
            record.select_invoice_line_id = record.action == 'sell' and len(record.invoice_id.invoice_line_ids) > 1

    @api.onchange('action')
    def _onchange_action(self):
        if self.action == 'sell' and self.asset_id.children_ids.filtered(lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError(_("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s)."))

    @api.depends('asset_id', 'invoice_id', 'invoice_line_id')
    def _compute_gain_or_loss(self):
        for record in self:
            line = record.invoice_line_id or len(record.invoice_id.invoice_line_ids) == 1 and record.invoice_id.invoice_line_ids or self.env['account.move.line']
            if record.asset_id.value_residual < abs(line.balance):
                record.gain_or_loss = 'gain'
            elif record.asset_id.value_residual > abs(line.balance):
                record.gain_or_loss = 'loss'
            else:
                record.gain_or_loss = 'no'

    def do_action(self):
        self.ensure_one()
        invoice_line = self.env['account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
        return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)
