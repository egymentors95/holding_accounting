# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    activate_initial_engagement = fields.Boolean(related='company_id.activate_initial_engagement', readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    activate_initial_engagement = fields.Boolean(string='Activate Initial Engagement', default=False)
