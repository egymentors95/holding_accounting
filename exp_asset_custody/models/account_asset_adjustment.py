# -*- coding: utf-8 -*-
# © Copyright (C) 2021 Expert Co. Ltd(<http:/www.exp-sa.com>)

from odoo import api, fields, models, exceptions,  _


class AccountAssetAdjustment(models.Model):
    _inherit = 'account.asset.adjustment'

    type = fields.Selection(
        selection_add=[('department', 'By Department'),
                       ('employee', 'By Employee'),
                       ('location', 'By Location')],
        states={'draft': [('readonly', False)]},
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        states={'draft': [('readonly', False)]},
        readonly=True,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        states={'draft': [('readonly', False)]},
        readonly=True,
    )
    location_id = fields.Many2one(
        comodel_name='account.asset.location',
        states={'draft': [('readonly', False)]},
        readonly=True,
    )

    def build_domain(self):
        return self.type == 'employee' and [('employee_id', '=', self.employee_id.id)] or \
               (self.type == 'department' and [('department_id', '=', self.department_id.id)]) or \
               (self.type == 'location' and [('location_id', '=', self.location_id.id)]) or \
               super(AccountAssetAdjustment, self).build_domain()

    @api.onchange('type')
    def onchange_type(self):
        self.employee_id = False
        self.department_id = False
        self.location_id = False
        super(AccountAssetAdjustment, self).onchange_type()
