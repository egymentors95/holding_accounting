#  Copyright 2020 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError 
from odoo.osv import expression


class fiscalyears_periods(models.Model):
    _name = 'fiscalyears.periods'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', translate=True,tracking=True)
    opening = fields.Boolean(string='Opening', help='is it an opening period')
    date_from = fields.Date(string='Start Date', help='''the start of the period''',tracking=True)
    date_to = fields.Date(string='End Date', help='the end of the period',tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('open', 'Open'),
                                        ('closed', 'Closed'),
                                        ('cancel', 'Cancel')],
                             default='draft',
                             string='State', help='''the state of the current
                             period where \n draft is the new created \n
                             open is the current runing period \n
                             closed is means you can not assign any operation
                             in this period \n this ficalyear has been
                              canceled ''',tracking=True)
    fiscalyear_id = fields.Many2one(comodel_name='account.fiscal.year', string='Fiscalyear')
    moves_ids = fields.One2many(comodel_name='account.move',
                                inverse_name='period_id',
                                string='Moves', help='''the moves
                                    linked with the period''')


    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """
        check start date and end date to see if :
        start date come after end date or the range of
        the given period is crosing another period
        or crossing the fiscalyear date range
        """
        for obj in self:
            start_date = fields.Date.from_string(obj.date_from)
            end_date = fields.Date.from_string(obj.date_to)

            fiscalyear_start_date = fields.Date.from_string(
                obj.fiscalyear_id.date_from)

            fiscalyear_end_date = fields.Date.from_string(
                obj.fiscalyear_id.date_to)

            if start_date and end_date:
                if start_date > end_date:
                    raise ValidationError(
                        _('start date must be before end date'))

                if not obj.opening and\
                        (in_range(self, start_date) or in_range(self, end_date)):
                    raise ValidationError(
                        _('dates range can not cross with another period'))

            if start_date:
                if start_date < fiscalyear_start_date \
                        or end_date > fiscalyear_end_date:
                    raise ValidationError(
                        _('period range must be in the fiscalyear range'))

    @api.depends('date_from', 'date_to', 'state')
    def _get_name(self):
        """
        make the name of the record from start date and end date and state.
        """
        for rec in self:
            if rec.date_from and rec.date_to:
                # for translation purpose
                opening_str = _('opening')

                name = ('%s-%s') % (
                    str(fields.Date.from_string(rec.date_from).year),
                    str(fields.Date.from_string(rec.date_to).month))

                if rec.opening:
                    name = ('%s-%s') % (
                        str(fields.Date.from_string(rec.date_from).year),
                        opening_str)
                rec.name = name

    def cancel(self):
        """
        change state to cancel .
        """
        for rec in self:
            # operations code goes here
            rec.state = 'cancel'

    def close(self):
        """
        change state of the  period to close after make sure every linked operation is reached last state.
        """
        for rec in self:
            # operations code goes here
            rec.state = 'closed'

    def draft(self):
        """
        change state to draft .
        """
        for rec in self:
            rec.state = 'draft'

    def unlink(self):
        """
        delete fiscal years but they must be in draft state .
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _('You cannot delete a period not in draft state.'))

        self.env['ir.translation'].search([('name', '=', "fiscalyears.periods,name"),
                                           ('res_id', 'in', self.ids)]).unlink()
        return super(fiscalyears_periods, self).unlink()

    def open(self):
        """
        change state to open .
        """
        for rec in self:
            if rec.fiscalyear_id.state not in ['open']:
                raise ValidationError(
                    _('''You cannot open a period where the fiscalyear not in open state.'''))
            rec.state = 'open'

    def cancel(self):
        """
        change state to cancel.
        """
        for rec in self:
            if rec.moves_ids:
                raise ValidationError(
                    _('You can not cancel a period linked with moves'))
            rec.state = 'cancel'

    def close(self):
        """
        change state of the  period to close after make sure every linked operation is reached last state.
        """
        for rec in self:
            if not all(x == 'posted' for x in
                       rec.mapped('moves_ids.state')):
                raise ValidationError(
                    _('Make sure all linked moves have been posted.'))
            rec.state = 'closed'

def in_range(self, dt):
        """
        check a date in all fiscalyear/period date ranges.
        param td: date to check
        returns: boolean
            * true if the date hase occurred in previous fiscalyear/period,
            * False if the date hase not occurred in previous
            fiscalyear/period.
        """
        domain = [('id', '!=', self.id),
                  ('state', '!=', 'cancel'),
                  ('date_from', '!=', False),
                  ('date_to', '!=', False)]

        if dir(self).__contains__('opening'):
            domain += [('opening', '!=', True)]
        date_ranges = self.search(domain)
        for year in date_ranges:
            if dt == fields.Date.from_string(year.date_from):
                return True
            elif dt == fields.Date.from_string(year.date_to):
                return True
            elif dt > fields.Date.from_string(year.date_from) and dt < fields.Date.from_string(year.date_to):
                return True
        return False