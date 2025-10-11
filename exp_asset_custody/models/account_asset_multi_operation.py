# -*- coding: utf-8 -*-
# © Copyright (C) 2021 Expert Co. Ltd(<http:/www.exp-sa.com>)

from odoo import models, fields, api, exceptions, _

class AccountAssetMultiOperation(models.Model):
    _name = 'account.asset.multi.operation'
    _description = 'Asset Multi Operation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'barcodes.barcode_events_mixin']

    name = fields.Char(
        states={'draft': [('readonly', False)]},
        default='/', readonly=True
    )
    date = fields.Date(
        default=fields.Date.context_today,
        index=True, copy=False, readonly=True, required=True,
        states={'draft': [('readonly', False)]}
    )
    type = fields.Selection(
        selection=[('assignment', 'Assignment'),
                   ('release', 'Release'),
                   ('transfer', 'Transfer')],
        states={'draft': [('readonly', False)]},
        readonly=True, required=True
    )
    barcode = fields.Char(
        states={'in_progress': [('readonly', False)]},
        readonly=True,
    )
    responsible_user_id = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.user,
        states={'draft': [('readonly', False)]},
        readonly=True, required=True
    )
    responsible_department_id = fields.Many2one(
        comodel_name='hr.department',
    )
    new_employee_id = fields.Many2one(
        comodel_name='hr.employee',
        states={'draft': [('readonly', False)]},
        readonly=True, string='Employee',
    )
    new_department_id = fields.Many2one(
        comodel_name='hr.department',
        states={'draft': [('readonly', False)]},
        readonly=True, string='Department',
    )
    new_location_id = fields.Many2one(
        comodel_name='account.asset.location',
        states={'draft': [('readonly', False)]},
        readonly=True, string='Location',
    )
    manual = fields.Boolean()
    note = fields.Text(
        states={'draft': [('readonly', False)]},
        readonly=True, required=True
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('in_progress', 'In Progress'),
                   ('done', 'Done'),
                   ('cancel', 'Cancel')],
        required=True, default='draft'
    )
    operation_ids = fields.One2many(
        'account.asset.operation', 'multi_operation_id',
        states={'in_progress': [('readonly', False)]},
        readonly=False,
    )

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].with_context(
            ir_sequence_date=values['date']).next_by_code('asset.multi.operation.seq')
        return super(AccountAssetMultiOperation, self).create(values)

    def act_progress(self):
        self.state = 'in_progress'

    def act_confirm(self):
        if not self.operation_ids:
            raise exceptions.Warning(_('You can not confirm operation without lines.'))
        for opt in self.operation_ids:
            self.check_required_fields(opt)
            opt.act_confirm()
        self.state = 'done'

    def act_reject(self):
        self.state = 'cancel'

    def act_draft(self):
        self.state = 'draft'

    def get_asset_domain(self):
        if self.type == 'assignment':
            return [('status', 'in', ['new','available'])]
        elif self.type in ['transfer', 'release']:
            return [('status', 'in', ['assigned'])]
        return [('status', 'in', ['new', 'available', 'assigned', 'scrap'])]

    @api.onchange('new_employee_id')
    def onchange_new_employee(self):
        self.new_department_id = self.new_employee_id.department_id.id

    @api.onchange('barcode')
    def onchange_barcode(self):
        self.on_barcode_scanned(self.barcode)

    def on_barcode_scanned(self, barcode):
        if barcode:
            operation_vals = self.get_operation_vals()
            domain = self.get_asset_domain()
            assets = self.barcode and self.env['account.asset'].search(domain + [('barcode', '=', barcode)])
            self.barcode = False
            if not assets:
                raise exceptions.Warning(_('No asset found with the selected barcode'))
            for s in assets:
                operation_vals.update({
                    'asset_id': s.id,
                    'current_employee_id': s.employee_id.id,
                    'current_department_id': s.department_id.id,
                    'current_location_id': s.location_id.id,
                    #'state': 'submit',
                })
            self.operation_ids = [(0, 0, operation_vals)]

    def get_operation_vals(self):
        return {
            'state': 'draft',
            'type': self.type,
            'date': self.date,
            'note': self.note,
            'multi_operation_id': self.id,
            'user_id': self.responsible_user_id.id,
            'new_employee_id': self.new_employee_id.id,
            'new_department_id': self.new_department_id.id,
            'new_location_id': self.new_location_id.id,
        }

    def check_required_fields(self, operation):
        if not operation.asset_id:
            raise exceptions.Warning(_('Make sure you choose an asset in all operation line.'))
        elif not operation.return_date and operation.custody_period == 'temporary':
            raise exceptions.Warning(_('Make sure you enter the return date for all temporary custodies.'))
        elif not operation.custody_type and operation.type in ['assignment', 'transfer']:
            raise exceptions.Warning(_('Make sure you choose custody type for all operation lines.'))
        elif not operation.custody_period and operation.type in ['assignment', 'transfer']:
            raise exceptions.Warning(_('Make sure you choose custody period for all operation lines.'))