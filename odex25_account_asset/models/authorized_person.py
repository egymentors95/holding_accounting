from odoo import models, fields, api


class AuthorizedPerson(models.Model):
    _name = 'authorized.person'
    _description = 'Authorized Person'
    _rec_name = 'name'
    name = fields.Char(string='Name', required=True)
    signature = fields.Binary(string='Signature',widget='signature',)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    authorized_person_id = fields.Many2one(
        'authorized.person', string='Authorized Person',
        help='The authorized person for this partner',
        ondelete='set null', index=True)

    signature = fields.Binary(
        related='authorized_person_id.signature',
        string='Signature',
        help='Signature of the authorized person',
        readonly=False, store=True)
