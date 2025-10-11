from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BudgetGeneralClassification(models.Model):
    _name = 'budget.general.classification'
    _description = 'General Classification'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetHigherManagement(models.Model):
    _name = 'budget.higher.management'
    _description = 'Higher Management'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetManagementClassification(models.Model):
    _name = 'budget.management.classification'
    _description = 'Management Classification'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetClassification(models.Model):
    _name = 'budget.classification'
    _description = 'Classification'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetSubManagement(models.Model):
    _name = 'budget.sub.management'
    _description = 'Sub Management'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetProgram(models.Model):
    _name = 'budget.program'
    _description = 'Program'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetAccountProgram(models.Model):
    _name = 'budget.account.program'
    _description = 'Account Program'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class BudgetDoor(models.Model):
    _name = 'budget.door'
    _description = 'Door'
    _rec_name = 'name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError('The code must be unique.')


class AccountBudget(models.Model):
    _inherit = 'crossovered.budget'

    general_classification_id = fields.Many2one('budget.general.classification', string='General Classification')
    higher_management_id = fields.Many2one('budget.higher.management', string='Higher Management')
    management_classification_id = fields.Many2one('budget.management.classification',
                                                   string='Management Classification')
    classification_id = fields.Many2one('budget.classification', string='Classification')
    sub_management_id = fields.Many2one('budget.sub.management', string='Sub Management')
    program_id = fields.Many2one('budget.program', string='Program')
    account_program_id = fields.Many2one('budget.account.program', string='Account Program')
    door_id = fields.Many2one('budget.door', string='Door')


class AccountBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    general_classification_id = fields.Many2one('budget.general.classification', string='General Classification',
                                                related='crossovered_budget_id.general_classification_id', store=True)
    higher_management_id = fields.Many2one('budget.higher.management', string='Higher Management',
                                           related='crossovered_budget_id.higher_management_id', store=True)
    management_classification_id = fields.Many2one('budget.management.classification',
                                                   string='Management Classification',
                                                   related='crossovered_budget_id.management_classification_id',
                                                   store=True)
    classification_id = fields.Many2one('budget.classification', string='Classification',
                                        related='crossovered_budget_id.classification_id', store=True)
    sub_management_id = fields.Many2one('budget.sub.management', string='Sub Management',
                                        related='crossovered_budget_id.sub_management_id', store=True)
    program_id = fields.Many2one('budget.program', string='Program', related='crossovered_budget_id.program_id',
                                 store=True)
    account_program_id = fields.Many2one('budget.account.program', string='Account Program',
                                         related='crossovered_budget_id.account_program_id', store=True)
    door_id = fields.Many2one('budget.door', string='Door', related='crossovered_budget_id.door_id', store=True)
