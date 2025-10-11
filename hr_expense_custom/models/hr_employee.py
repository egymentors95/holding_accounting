from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # expense_manager_id = fields.Many2one(
    #     compute='', 
    #     store=False, 
    #     related='partner_id.user_id'
    # )


    @api.depends('parent_id')
    def _compute_expense_manager(self):
        for employee in self:
            manager = employee.parent_id.user_id
            employee.expense_manager_id = manager
