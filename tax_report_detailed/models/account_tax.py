from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    government_type = fields.Selection(string="Governmental Type",
                                       selection=[('gov', 'Governmental'), ('not_gov', 'Non-Governmental'), ],
                                       required=False, )
