# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _, tools, _lt
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    gain_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', id)]",
                                      help="Account used to write the journal item in case of gain while selling an asset")
    loss_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', id)]",
                                      help="Account used to write the journal item in case of loss while selling an asset")


class ResPartner(models.Model):
    _inherit = "res.partner"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 help="Company of the partner. This field is used to determine the company of the partner when creating a new partner. It is also used to filter the partner's records in the company context.")

    _sql_constraints = [
        ('check_name', "CHECK( (type='contact' AND name IS NOT NULL) or (type!='contact') )",
         'Contacts require a name'),
    ]
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 help="Company of the purchase order. This field is used to determine the company of the purchase order when creating a new purchase order. It is also used to filter the purchase order's records in the company context.")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, states=READONLY_STATES,
                                 change_default=True, tracking=True,
                                 domain="[('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference. a7a")
