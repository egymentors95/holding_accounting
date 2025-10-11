# -*- coding: utf-8 -*-
# © Copyright (C) 2021 Expert Co. Ltd(<http:/www.exp-sa.com>)

from odoo import api, fields, models, exceptions,  _


class AccountAssetAdjustment(models.Model):
    _name = 'account.asset.adjustment'
    _inherit = ['barcodes.barcode_events_mixin',"mail.thread", "mail.activity.mixin"]
    _description = 'Asset Adjustment'

    name = fields.Char(
        states={'draft': [('readonly', False)]},
        readonly=True, required=True,tracking=True
    )
    date = fields.Date(
        default=fields.Date.context_today,
        index=True, copy=False, readonly=True, required=True,tracking=True,
        states={'draft': [('readonly', False)]}
    )
    type = fields.Selection(
        selection=[('product', 'By Product'),
                   ('model', 'By Model')],
        states={'draft': [('readonly', False)]},
        readonly=True,tracking=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        domain=[('property_account_expense_id.can_create_asset', '=', True),
                ('property_account_expense_id.user_type_id.internal_group', '=', 'asset')],
        states={'draft': [('readonly', False)]},
        readonly=True,tracking=True
    )
    model_id = fields.Many2one(
        comodel_name='account.asset',
        domain=[('asset_type', '=', 'purchase'), ('state', '=', 'model')],
        states={'draft': [('readonly', False)]},
        readonly=True,tracking=True
    )
    barcode = fields.Char(
        states={'in_progress': [('readonly', False)]},
        readonly=True,tracking=True
    )
    adjustment_line_ids = fields.One2many(
        'account.asset.adjustment.line', 'adjustment_id',
        states={'in_progress': [('readonly', False)]},
        readonly=True,tracking=True
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('in_progress', 'In Progress'),
                   ('done', 'Done'),
                   ('cancel', 'Cancel')],
        required=True, default='draft',tracking=True
    )

    def build_domain(self):
        return (self.type == 'product' and [('product_id', '=', self.product_id.id)]) or \
               (self.type == 'model' and [('model_id', '=', self.model_id.id)]) or []

    def act_progress(self):
        domain = self.build_domain()
        assets = self.env['account.asset'].search(domain+[('asset_type', '=', 'purchase'),
                                                          ('state', '!=', 'model'), ('parent_id', '=', False)])
        self.adjustment_line_ids = [(0, 0, {'asset_id': s.id}) for s in assets]
        self.state = 'in_progress'

    def act_done(self):
        if self.adjustment_line_ids.search([('adjustment_id', '=', self.id), ('exist', '=', True), ('asset_status2', '=', False)]):
            raise exceptions.Warning(_('You should enter the asset status for all assets that marked as exist.'))
        self.barcode = False
        self.state = 'done'

    def act_cancel(self):
        self.state = 'cancel'

    def act_draft(self):
        self.state = 'draft'
        self.adjustment_line_ids.unlink()

    @api.onchange('type')
    def onchange_type(self):
        self.product_id = False
        self.model_id = False

    def on_barcode_scanned(self, barcode):
        if barcode:
            line = self.adjustment_line_ids.filtered(lambda x: x.barcode == barcode)
            if not line:
                raise exceptions.Warning(_('No asset found with the selected barcode'))
            for l in line:
                l.exist = True

    @api.onchange('barcode')
    def onchange_barcode(self):
        self.on_barcode_scanned(self.barcode)


class AccountAssetAdjustmentLine(models.Model):
    _name = 'account.asset.adjustment.line'
    _description = 'Asset Adjustment Line'

    adjustment_id = fields.Many2one(comodel_name='account.asset.adjustment',tracking=True)
    asset_id = fields.Many2one(comodel_name='account.asset',tracking=True)
    barcode = fields.Char(related='asset_id.barcode',tracking=True)
    serial_no = fields.Char(related='asset_id.serial_no',tracking=True)
    asset_status = fields.Selection(selection=[('good', 'Good'), ('scrap', 'Scrap')],tracking=True)
    asset_status2  = fields.Many2one(
        comodel_name='asset.state2',
        string='Asset Status',tracking=True)
    exist = fields.Boolean(string="Exist?",tracking=True)
class AccountAssestatus(models.Model):
    _name = 'asset.state2'
    name = fields.Char(string='Name')
#
