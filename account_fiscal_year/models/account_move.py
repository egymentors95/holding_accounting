# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2018 (<http://www.exp-sa.com/>).
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError
import datetime
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang

class AccountMove(models.Model):
    _name = "account.move"
    _inherit = "account.move"

    period_id = fields.Many2one('fiscalyears.periods',
                                string='Period', readonly=True,
                                states={'draft': [('readonly', False)]},
                                help='''The fiscalyear period
                                used for this receipt.''')

    @api.onchange('date')
    def _onchange_date_period(self):
        for rec in self:
            if rec.date:
                periods = self.env['fiscalyears.periods'].search(
                    [('state', '=', 'open'),
                     ('date_from', '<=', rec.date),
                     ('date_to', '>=', rec.date)])
                if periods:
                    rec.period_id = periods[0].id
                else:
                    raise ValidationError(
                        _('There is no openning fiscal year periods in this date.'))

    # @api.constrains('date', 'period_id')
    # def _check_date_period(self):
    #     """
    #     Check date and period_id are in the same date range
    #     """
    #     for rec in self:
    #         if rec.date and rec.period_id:
    #             date = fields.Date.from_string(rec.date)
    #             period_start_date = fields.Date.from_string(
    #                 rec.period_id.date_from)
    #             period_end_date = fields.Date.from_string(
    #                 rec.period_id.date_to)
    #             if not (date >= period_start_date and
    #                     date <= period_end_date):
    #                 raise ValidationError(
    #                     _('''Date and period must be in the same date range'''))
    #         else:
    #             raise ValidationError(
    #                 _('''You must enter date and period for this record'''))

    def _post(self, soft=True):
        """Post/Validate the documents."""
        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            future_moves.auto_post = True
            for move in future_moves:
                msg = _('This move will be posted at the accounting date: %(date)s',
                        date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self


        for move in to_post:
            if not move.period_id:
                period = self.env['fiscalyears.periods'].search([
                    ('date_from', '<=', move.date),
                    ('date_to', '>=', move.date),
                ], limit=1)

                if period:
                    move.period_id = period.id
                else:
                    raise UserError(_("No valid open period found for the date: %s") % move.date)
        return super(AccountMove, self)._post(soft=soft)


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"
    
    period_id = fields.Many2one('fiscalyears.periods',
                                related='move_id.period_id', store=True,
                                string='Period', related_sudo=False,
                                help='''The fiscalyear period
                                used for this move line.''')
