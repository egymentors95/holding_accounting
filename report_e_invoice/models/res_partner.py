from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commercial_register = fields.Char('Commercial Register')

    other_id_type = fields.Selection([('id_card', 'Identity Card'),
                                      ('passport', 'Passport'),
                                      ('cr', 'Commercial Register')], "Other ID")
    id_number = fields.Char(
        string='Identity NO',
    )
