from odoo import models, fields, api, _, exceptions
from odoo import SUPERUSER_ID


# from datetime import datetime , date


class EmployeeCustody(models.Model):
    _inherit = 'custom.employee.custody'

    state = fields.Selection(selection=[
        ("draft", _("Draft")),
        ("submit", _("send")),
        ("direct", _("Direct Manager")),
        ("admin", _("Human Resources Manager")),
        ("wait", _("Wait Assignment")),
        ("assign", _("Assignment")),
        ("wait_release", _("Wait Release")),
        ("done", _("Return Done")),
        ("refuse", _("Refuse"))
    ], default='draft')

    asset_line_ids = fields.One2many('asset.custody.line', 'asset_custody_line', required=True)
    asset_assign_count = fields.Integer(compute='_asset_assign_count', string='Asset Assignment')
    asset_release_count = fields.Integer(compute='_asset_release_count', string='Asset Release')

    def create_asset_custody(self):
        for i in self.asset_line_ids:
            data = {
                'date': self.current_date,
                'asset_id': i.asset_id.id,
                'type': 'assignment',
                'custody_type': i.custody_type,
                'custody_period': i.custody_period,
                'state': 'draft',
                'user_id': self.env.uid,
                'new_employee_id': self.employee_id.id,
                'new_department_id': self.department_id.id,
                'emp_asset_custody_id': self.id,

            }
            self.env['account.asset.operation'].create(data)

    def asset_custody_release(self):
        for i in self.asset_line_ids:
            data = {
                'name': i.asset_id.name,
                'date': self.current_date,
                'asset_id': i.asset_id.id,
                'type': 'release',
                'custody_type': i.custody_type,
                'custody_period': i.custody_period,
                'state': 'draft',
                'user_id': self.env.uid,
                'current_employee_id': self.employee_id.id,
                'new_employee_id': self.employee_id.id,
                'current_department_id': self.department_id.id,
                'emp_asset_custody_id': self.id,

            }
            self.env['account.asset.operation'].create(data)

    def _asset_assign_count(self):
        self.asset_assign_count = len(
            self.env['asset.custody.line'].search([('asset_custody_line', '=', self.id)]))

    def _asset_release_count(self):
        self.asset_release_count = len(
            self.env['asset.custody.line'].search([('asset_custody_line', '=', self.id)]))

    def approve(self):
        if not self.asset_line_ids:
            raise exceptions.Warning(_('Please Select an asset'))
        self.create_asset_custody()
        self.write({'state': 'wait'})

    def done(self):
        self.asset_custody_release()
        self.state = "wait_release"


class EmployeeCustodyLine(models.Model):
    _name = 'asset.custody.line'

    # Asset custody fields
    type = fields.Selection([('assignment', 'Assignment')])
    custody_type = fields.Selection(selection=[('personal', 'Personal'), ('general', 'General')])
    custody_period = fields.Selection(selection=[('temporary', 'Temporary'), ('permanent', 'Permanent')])
    return_date = fields.Date()
    date = fields.Date()
    asset_id = fields.Many2one('account.asset')
    asset_custody_line = fields.Many2one(comodel_name='custom.employee.custody')  # Inverse field

    @api.model
    def create(self, vals):
        res = super(EmployeeCustodyLine, self).create(vals)
        if res.asset_id and res.asset_id.status in ['new', 'available']:
            res.asset_id.write({'status': 'reserved'})
        return res

    def unlink(self):
        assets = self.mapped('asset_id')
        result = super(EmployeeCustodyLine, self).unlink()
        if result and assets:
            assets.write({'status': 'available'})
        return result


class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search(
                [('res_model', '=', vals.get('res_model')), ('res_id', '=', vals.get('res_id')),
                 ('partner_id', '=', vals.get('partner_id'))])

            if len(dups):
                for p in dups:
                    p.unlink()

        res = super(Followers, self).create(vals)

        return res
