# -*- coding: utf-8 -*-

from odoo.api import Environment, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import _


def _check_modules(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    if env['ir.module.module'].search([('name', '=', 'l10n_exp'),('state', '!=', 'installed')]):
        module = env['ir.module.module'].search([
            ('name', '=', 'account_chart_of_accounts'),
            ('state', '=', 'installed')
        ])
        if not module:
            raise ValidationError(_('Hierarchy Chart Of Accounts (account_chart_of_accounts) must be install before installing this module.'))

        module = env['ir.module.module'].search([
            ('name', '=', 'l10n_multilang'),
            ('state', '=', 'installed')
        ])
        if not module:
            raise ValidationError(_('Multi Language Chart of Accounts (l10n_multilang) must be install before installing this module.'))