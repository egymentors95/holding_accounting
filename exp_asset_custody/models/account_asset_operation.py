# -*- coding: utf-8 -*-
# © Copyright (C) 2021 Expert Co. Ltd(<http:/www.exp-sa.com>)

from odoo import models, fields, api, exceptions, _


class AccountAssetOperation(models.Model):
    _name = 'account.asset.operation'
    _description = 'Asset Operation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    multi_operation_id = fields.Many2one(comodel_name='account.asset.multi.operation')
    name = fields.Char(required=True, default='/')
    type = fields.Selection(selection=[('assignment', 'Assignment'), ('release', 'Release'),
                                       ('transfer', 'Transfer')], required=True)
    date = fields.Date(default=fields.Date.context_today, index=True, copy=False, readonly=True, required=True,
                       states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(comodel_name='res.users',default=lambda self: self.env.user,
                              states={'draft': [('readonly', False)]},string='Responsible',readonly=True)
    asset_id = fields.Many2one(comodel_name='account.asset')
    statea = fields.Selection(related='asset_id.status')
    barcode = fields.Char(compute="_compute_related_fields", store=True)
    department_id = fields.Many2one(comodel_name='hr.department',string='Responsible Department',
                                    compute="_compute_related_fields", store=True)
    model_id = fields.Many2one(comodel_name='account.asset',compute="_compute_related_fields",store=True)
    state = fields.Selection(selection=[('draft', 'Draft'),('submit', 'Submit'),('done', 'Done'),('pending', 'Pending')
                                        ,('cancel', 'Cancel')],required=True, default='draft')
    note = fields.Text(states={'draft': [('readonly', False)]},readonly=True,)
    # Asset Custody Operation
    custody_type = fields.Selection(selection=[('personal', 'Personal'), ('general', 'General')],
                                    states={'draft': [('readonly', False)]},readonly=True,)
    custody_period = fields.Selection(selection=[('temporary', 'Temporary'), ('permanent', 'Permanent')],
                                      states={'draft': [('readonly', False)]},readonly=True)
    return_date = fields.Date(states={'draft': [('readonly', False)]},readonly=True)
    current_employee_id = fields.Many2one(comodel_name='hr.employee',
                                          states={'draft': [('readonly', False)]},readonly=True, string='Employee')
    current_department_id = fields.Many2one(comodel_name='hr.department',states={'draft': [('readonly', False)]},
                                            readonly=True, string='Department', )
    current_location_id = fields.Many2one(comodel_name='account.asset.location',states={'draft': [('readonly', False)]},
                                          readonly=True, string='Location')
    new_employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    new_department_id = fields.Many2one(comodel_name='hr.department', string='Department', )
    new_location_id = fields.Many2one(comodel_name='account.asset.location', string='Location')
    amount = fields.Float(states={'draft': [('readonly', False)]}, readonly=True, )
    asset_status = fields.Selection(selection=[('good', 'Good'), ('scrap', 'Scrap')],
                                    states={'draft': [('readonly', False)]}, readonly=True, )
    asset_statuso = fields.Selection(related='asset_id.status')
    asset_status2  = fields.Many2one(
        comodel_name='asset.states',
        string='Asset Status',states={'draft': [('readonly', False)]})
    product_id = fields.Many2one(comodel_name='product.product',
                                 domain=[('property_account_expense_id.can_create_asset', '=', True),
                                         ('property_account_expense_id.user_type_id.internal_group', '=', 'asset')],
                                 states={'draft': [('readonly', False)]}, readonly=True)

    def action_read_operation(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.operation',
            'res_id': self.id,
        }

    @api.depends('asset_id', 'asset_id.model_id', 'asset_id.responsible_dept_id', 'asset_id.barcode')
    def _compute_related_fields(self):
        for operation in self:
            operation.barcode = operation.asset_id.barcode
            operation.model_id = operation.asset_id.model_id.id
            operation.department_id = operation.asset_id.responsible_dept_id.id

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].with_context(
            ir_sequence_date=values['date']).next_by_code('asset.operation.seq')
        return super(AccountAssetOperation, self).create(values)

    def unlink(self):
        if self.search([('state', '!=', 'draft'), ('id', 'in', self.ids)]):
            raise exceptions.Warning(_('Only draft operations can be deleted.'))
        return super(AccountAssetOperation, self).unlink()

    @api.model
    def _get_tracked_fields(self):
        fields = self.fields_get()
        dels = [f for f in fields if f in models.LOG_ACCESS_COLUMNS or f.startswith('_') or f == 'id']
        for x in dels:
            del fields[x]
        return set(fields)

    @api.onchange('new_employee_id')
    def onchange_new_employee(self):
        self.new_department_id = self.new_employee_id.department_id.id

    @api.onchange('asset_id')
    def onchange_asset(self):
        self.current_employee_id = self.asset_id.employee_id.id
        self.current_department_id = self.asset_id.department_id.id
        self.current_location_id = self.asset_id.location_id.id

    def act_submit(self):
        self.state = 'submit'

    def act_confirm(self):
        if not self.asset_id:
            raise exceptions.Warning(_('Asset is required to confirm this operation.'))
        if self.type in ('assignment', 'release', 'transfer'):
            self.custody_confirm()
        self.state = 'done'

    def act_reject(self):
        self.state = 'pending'

    def act_cancel(self):
        self.state = 'cancel'

    def act_draft(self):
        self.state = 'draft'

    def custody_confirm(self):
        self.asset_id.employee_id = self.new_employee_id.id
        self.asset_id.department_id = self.new_department_id.id
        self.asset_id.location_id = self.new_location_id.id
        self.asset_id.custody_type = self.custody_type
        self.asset_id.custody_period = self.custody_period
        self.asset_id.return_date = self.return_date
        self.asset_id.purpose = self.note
        if self.type == 'assignment':
            self.asset_id.status = 'assigned'
        elif self.type == 'release':
            self.asset_id.status = 'available'


"""
    def sell_dispose_confirm(self):
        super(AccountAssetOperation, self).sell_dispose_confirm()
        self.asset_id.custody_type = False
        self.asset_id.custody_period = False
        self.asset_id.purpose = False
        self.asset_id.return_date = False
        self.asset_id.department_id = False
        self.asset_id.employee_id = False
        self.asset_id.location_id = False
        self.asset_id.status = False
    """
class AccountAssestatus(models.Model):
    _name = 'asset.states'
    name = fields.Char(string='Name')
