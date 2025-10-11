from odoo import fields, models, api, _
from odoo.exceptions import Warning


class OpeningAccountMoveWizard(models.TransientModel):
    _inherit = 'account.financial.year.op'

    period_id = fields.Many2one('fiscalyears.periods')

    @api.onchange('opening_date')
    def _onchange_date_period(self):
        for wiz in self:
            print(wiz, 'wiz')
            if wiz.date:
                periods = self.env['fiscalyears.periods'].search(
                    [('state', '=', 'open'),
                     ('date_from', '<=', wiz.opening_date),
                     ('date_to', '>=', wiz.opening_date)])
                if periods:
                    wiz.period_id = periods[0].id
                else:
                    raise Warning(
                        _('No Open fiscal year periods in this date.'))
