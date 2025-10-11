# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2018 (<http://www.exp-sa.com/>).
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BudgetOperations(models.Model):
    """
    this model used to make operations on budget
    """
    _name = 'budget.operations'
    _description = 'Budget Operations'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default='/')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    from_crossovered_budget_id = fields.Many2one(comodel_name='crossovered.budget', string='Budget', tracking=True,copy=False)
    from_budget_line_id = fields.Many2one(comodel_name='crossovered.budget.lines', string='Cost Center', tracking=True,copy=False)
    to_crossovered_budget_id = fields.Many2one(comodel_name='crossovered.budget', string='Budget', tracking=True,copy=False)
    to_budget_line_id = fields.Many2one(comodel_name='crossovered.budget.lines', string='Cost Center', tracking=True,copy=False)
    amount = fields.Monetary(string='Amount', tracking=True)
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', readonly=True, required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirmed', 'Confirmed')],
                             default='draft', string='Status', readonly=True, tracking=True,copy=False)
    type = fields.Selection(selection=[('unlock', 'Unlock'), ('transfer', 'Transfer')], default='transfer',
                            string='type', readonly=True, tracking=True)
    date = fields.Date()
    from_reserved = fields.Boolean(string='Reserve?', tracking=True,copy=False)
    from_budget_post_id = fields.Many2one(comodel_name='account.budget.post', string='Budget Post', tracking=True,copy=False)
    to_budget_post_id = fields.Many2one(comodel_name='account.budget.post', string='Budget Post', tracking=True,copy=False)
    operation_type = fields.Selection(
        selection=[('transfer', 'Transfer'), ('increase', 'Increase'), ('decrease', 'Decrease')],
        default='transfer', string='Operation Type', required=True, tracking=True)
    purchase_remind = fields.Monetary(string='Purchase Remind', tracking=True)

    @api.constrains('purchase_remind','amount')
    def _amount_can_not_be_less_than_zero(self):
        for rec in self:
            if rec.purchase_remind < 0 or rec.amount < 0:
                raise ValidationError(_('''The amount can not be less than zero.'''))

    @api.onchange('from_crossovered_budget_id', 'operation_type')
    def get_budget_domain_year(self):
        for rec in self:
            domain = [('id', '=', False)]
            if rec.operation_type == 'transfer' and rec.from_crossovered_budget_id:
                date_to = rec.from_crossovered_budget_id.date_to
                record = rec.env['crossovered.budget'].sudo().search([('date_to', '>', str(date_to))])
                if record:
                    domain = [('id', 'in', record.mapped('crossovered_budget_line.general_budget_id').ids)]
            else:
                domain = [('id', 'in', rec.env['account.budget.post'].sudo().search([]).ids)]
            return {'domain': {'to_budget_post_id': domain}}

    @api.model
    def create(self, values):
        sequence_code = 'budget_operation.seq'
        values['name'] = self.env['ir.sequence'].with_context(
            ir_sequence_date=values['date']).next_by_code(sequence_code)
        return super(BudgetOperations, self).create(values)

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        if self.operation_type == 'increase':
            self.from_crossovered_budget_id = False
            self.from_budget_line_id = False
            self.from_budget_post_id = False
            self.from_reserved = False

    @api.onchange('from_crossovered_budget_id', 'to_crossovered_budget_id', 'date')
    def _onchange_budget_check_period(self):
        if self.from_crossovered_budget_id and self.date:
            if self.from_crossovered_budget_id.date_from > self.date or self.from_crossovered_budget_id.date_to < self.date:
                raise ValidationError(
                    _('The date must be between the budget %s post period') % (self.from_crossovered_budget_id.name))

        if self.to_crossovered_budget_id and self.date:
            if self.to_crossovered_budget_id.date_from > self.date or self.to_crossovered_budget_id.date_to < self.date:
                raise ValidationError(
                    _('The date must be between the budget %s post period') % (self.from_crossovered_budget_id.name))

    @api.onchange('from_budget_post_id')
    def _onchange_from_budget_post(self):
        domain = [('id', 'in', [])]
        if self.from_budget_post_id:
            budget_line_obj = self.env['crossovered.budget.lines']
            budget_line = budget_line_obj.read_group([('general_budget_id', '=', self.from_budget_post_id.id)],
                                                     ['crossovered_budget_id'], ['crossovered_budget_id'])
            domain = [('id', 'in', [bl['crossovered_budget_id'][0] for bl in budget_line])]
        self.from_crossovered_budget_id = False
        self.from_budget_line_id = False
        return {'domain': {'from_crossovered_budget_id': domain}}

    @api.onchange('to_budget_post_id')
    def _onchange_to_budget_post(self):
        domain = [('id', 'in', [])]
        if self.to_budget_post_id:
            budget_line_obj = self.env['crossovered.budget.lines']
            search_domain = [('general_budget_id', '=', self.to_budget_post_id.id)]
            if self.operation_type == 'transfer' and self.from_crossovered_budget_id.date_to:
                search_domain += [('date_to', '>', str(self.from_crossovered_budget_id.date_to))]
            budget_line = budget_line_obj.search(search_domain)
            domain = [('id', 'in', budget_line.mapped('crossovered_budget_id').ids)]
        self.to_crossovered_budget_id = False
        self.to_budget_line_id = False
        return {'domain': {'to_crossovered_budget_id': domain}}

    @api.onchange('from_crossovered_budget_id')
    def _onchange_from_crossovered_budget(self):
        return {
            'domain': {
                'from_budget_line_id':
                    [('crossovered_budget_id', '=', self.from_crossovered_budget_id.id),
                     ('general_budget_id', 'in', [self.from_budget_post_id.id])]
            }
        }

    @api.onchange('to_crossovered_budget_id')
    def _onchange_to_crossovered_budget(self):
        return {
            'domain': {
                'to_budget_line_id':
                    [('crossovered_budget_id', '=', self.to_crossovered_budget_id.id),
                     ('general_budget_id', 'in', [self.to_budget_post_id.id])]
            }
        }

    def to_draft(self):
        self.state = 'draft'

    def confirm(self):
        if self.from_crossovered_budget_id and self.date and self.operation_type in ['transfer', 'decrease']:
            if self.from_crossovered_budget_id.date_from > self.date or self.from_crossovered_budget_id.date_to < self.date:
                raise ValidationError(
                    _('The date must be between the budget %s post period') % (self.from_crossovered_budget_id.name))

        if self.to_crossovered_budget_id and self.date and self.operation_type in ['transfer', 'increase']:
            if self.to_crossovered_budget_id.date_from > self.date or self.to_crossovered_budget_id.date_to < self.date:
                raise ValidationError(
                    _('The date must be between the budget %s post period') % (self.from_crossovered_budget_id.name))

        if self.to_crossovered_budget_id.state != 'done' and self.operation_type in ['transfer', 'increase']:
            raise ValidationError(
                _('You can  transfer to approved budget only'))

        if self.from_crossovered_budget_id.state != 'done' and self.operation_type in ['transfer', 'decrease']:
            raise ValidationError(
                _('You can  transfer to approved budget only'))

        if self.operation_type=='transfer':
            if abs(self.from_budget_line_id.final_amount) < abs(self.purchase_remind):
                raise ValidationError(
                    _('The amount must be less than or equal to the budget line final amount'))
        self.state = 'confirmed'
