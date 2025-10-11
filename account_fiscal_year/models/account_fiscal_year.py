#  Copyright 2020 Simone Rubino - Agile Business Group
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError 
from odoo.osv import expression
from dateutil.relativedelta import relativedelta



class AccountFiscalYear(models.Model):
    _name = "account.fiscal.year"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fiscal Year"
    _rec_name = "name"

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True
    )
    code = fields.Char(compute="_get_code", store=True, string='Code',
                       help='''The code of the fiscalyear like start date - end date - state ''',tracking=True)
    date_from = fields.Date(
        string="Start Date",
        required=True,
        help="Start Date, included in the fiscal year.",tracking=True
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
        help="Ending Date, included in the fiscal year.",tracking=True
    )
    state = fields.Selection(selection=[('draft', 'Draft'), ('open', 'Open'),
                                        ('closed', 'Closed'), ('cancel', 'Cancel')],
                             string='State', default='draft',
                             help='''the state of the current
                             fiscalyear where \n draft is the new created \n
                             open is the current runing fiscalyear \n
                             closed is means you can not assign any operation
                             in this fiscalyear \n this ficalyear has been canceled ''',tracking=True)
    type = fields.Selection(selection=[('monthly', 'Monthly'),
                                       ('quarterly', 'Quarterly'),
                                       ('biannual', 'Biannual'),
                                       ('annual', 'Annual')],
                            string='Type', default='monthly',
                            help='''the type of the fiscalyear \n
                            monthly : per month \n
                            quarterly : every three months\n
                            biannual : every six months\n
                            annual : every twelve months''',tracking=True)
    periods_ids = fields.One2many(comodel_name='fiscalyears.periods',
                                  inverse_name='fiscalyear_id', string='Periods',
                                  help='''the date periods used to assign operations''')
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.constrains("date_from", "date_to", "company_id")
    def _check_dates(self):
        """Check intersection with existing fiscal years."""
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.date_from
            date_to = fy.date_to
            if date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )

            domain = fy._get_overlapping_domain()
            overlapping_fy = self.search(domain, limit=1)
            if overlapping_fy:
                raise ValidationError(
                    _(
                        "This fiscal year '{fy}' "
                        "overlaps with '{overlapping_fy}'.\n"
                        "Please correct the start and/or end dates "
                        "of your fiscal years."
                    ).format(
                        fy=fy.display_name,
                        overlapping_fy=overlapping_fy.display_name,
                    )
                )

    def _get_overlapping_domain(self):
        """Get domain for finding fiscal years overlapping with self.

        The domain will search only among fiscal years of this company.
        """
        self.ensure_one()
        # Compare with other fiscal years defined for this company
        company_domain = [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
        ]

        date_from = self.date_from
        date_to = self.date_to
        # Search fiscal years intersecting with current fiscal year.
        # This fiscal year's `from` is contained in another fiscal year
        # other.from <= fy.from <= other.to
        intersection_domain_from = [
            "&",
            ("date_from", "<=", date_from),
            ("date_to", ">=", date_from),
        ]
        # This fiscal year's `to` is contained in another fiscal year
        # other.from <= fy.to <= other.to
        intersection_domain_to = [
            "&",
            ("date_from", "<=", date_to),
            ("date_to", ">=", date_to),
        ]
        # This fiscal year completely contains another fiscal year
        # fy.from <= other.from (or other.to) <= fy.to
        intersection_domain_contain = [
            "&",
            ("date_from", ">=", date_from),
            ("date_from", "<=", date_to),
        ]
        intersection_domain = expression.OR(
            [
                intersection_domain_from,
                intersection_domain_to,
                intersection_domain_contain,
            ]
        )

        return expression.AND(
            [
                company_domain,
                intersection_domain,
            ]
        )

    @api.depends('date_from', 'date_to')
    def _get_code(self):
        """
        make the code of the record from start date and end date.
        """
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.code = ('%s') % (str(fields.Date.from_string(rec.date_to).year))

    def create_periods(self):
        """
        create fiscalyear periods accoring to configuration.
        returns: boolean
            * true if the periods has created sucssesfly,
            * exception if any error happend.
        """
        monthly = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ar_monthly = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                      "يوليو", "أغسطس", "سبتمير", "أكتوبر", "نوفمبر", "ديسمبر"]
        quarterly = ["Q1", "Q2", "Q3", "Q4"]
        ar_quarterly = ["الربع الأول", "الربع التاني", "الربع الثالث", "الربع الرابع"]
        for rec in self:
            if not rec.type:
                raise ValidationError(
                    _('You Must Enter The Fiscalyear Type To Create Periods'))
            type_dict = {'monthly': 1, 'quarterly': 3,
                         'biannual': 6, 'annual': 12}
            interval = type_dict.get(rec.type, False)

            if not interval:
                raise ValidationError(
                    _('You Must Enter The Fiscalyear Type To Create Periods'))

            periods_obj = self.env['fiscalyears.periods']

            rec.periods_ids.unlink()
            all_periods = self.get_periods(interval)
            pid = periods_obj.create({
                'name': rec.name + "-"+"Opening",
                'fiscalyear_id': rec.id,
                'date_from': rec.date_from,
                'date_to': rec.date_from,
                'opening': True,
            })

            # insert opening period translations
            query = """ INSERT INTO ir_translation (lang, type, name, res_id, src, value, state)
                        SELECT l.code, 'model', %(name)s, %(res_id)s, %(src)s, %(value)s, %(state)s
                        FROM res_lang l
                        WHERE l.active AND l.code != 'en_US' AND NOT EXISTS (
                            SELECT 1 FROM ir_translation
                            WHERE lang=l.code AND type='model' AND name=%(name)s AND res_id=%(res_id)s
                        );
                                UPDATE ir_translation SET src=%(src)s, value=%(value)s
                                WHERE type='model' AND name=%(name)s AND res_id=%(res_id)s;
                    """
            self._cr.execute(query, {
                'name': "fiscalyears.periods,name",
                'res_id': pid.id,
                'src': pid.name,
                'value': rec.name + "-"+u"فترة أفتتاحية",
                'state': "translated"
            })

            count = 0
            while True:
                try:
                    period = next(all_periods)
                    name = (rec.type == "monthly" and monthly[count]) or \
                           (rec.type == "quarterly" and quarterly[count]) or str(count+1)
                    ar_name = (rec.type == "monthly" and ar_monthly[count]) or \
                           (rec.type == "quarterly" and ar_quarterly[count]) or str(count+1)
                    pid = periods_obj.create({
                        'name': rec.name + "-" + name,
                        'fiscalyear_id': rec.id,
                        'date_from': period[0],
                        'date_to': period[1],
                    })
                    # insert period name translations
                    query = """ INSERT INTO ir_translation (lang, type, name, res_id, src, value, state)
                                SELECT l.code, 'model', %(name)s, %(res_id)s, %(src)s, %(value)s, %(state)s
                                FROM res_lang l
                                WHERE l.active AND l.code != 'en_US' AND NOT EXISTS (
                                    SELECT 1 FROM ir_translation
                                    WHERE lang=l.code AND type='model' AND name=%(name)s AND res_id=%(res_id)s
                                );
                                UPDATE ir_translation SET src=%(src)s, value=%(value)s
                                WHERE type='model' AND name=%(name)s AND res_id=%(res_id)s;
                            """
                    self._cr.execute(query, {
                        'name': "fiscalyears.periods,name",
                        'res_id': pid.id,
                        'src': pid.name,
                        'value': rec.name + "-" + ar_name,
                        'state': "translated"
                    })
                    count += 1
                except Exception as e:
                    break

    def get_periods(self, interval):
        """
        get all periods start dates and end dates pairs according to the configuration of fiscalyear .
        param interval: the length of the period in months
        returns: boolean
            * list of tuples containing start and end dates of each period
        """
        start_date = fields.Date.from_string(self.date_from)
        end_date = fields.Date.from_string(self.date_to)
        while True:
            delta = start_date + relativedelta(months=interval)
            delta = delta - relativedelta(days=1)

            if delta >= end_date:
                delta = end_date

            yield (start_date, delta)

            start_date = delta + relativedelta(days=1)
            if start_date >= end_date:
                break

    def open(self):
        """
        make sure periods have been created for each fiscalyear and change state to open .
        """
        for rec in self:
            if not rec.periods_ids:
                raise ValidationError(
                    _('you must create periods for this fiscal year'))
            rec.state = 'open'
            rec.periods_ids.filtered(lambda x: x.opening).write({'state': 'open'})

    def close(self):
        """
        change state of the fiscalyears and there periods to close .
        """
        for rec in self:
            if not all(x == 'closed' for x in
                       rec.mapped('periods_ids.state')):
                raise ValidationError(
                    _('you must close every period of this fiscal year'))
            rec.state = 'closed'

    def cancel(self):
        """
        change state to cancel .
        """
        for rec in self:
            rec.periods_ids.cancel()
            rec.state = 'cancel'

    def draft(self):
        """
        change state to draft .
        """
        for rec in self:
            rec.periods_ids.draft()
            rec.state = 'draft'

    def unlink(self):
        """
        delete fiscal years but they must be in draft state .
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _('You cannot delete a fiscal year not in draft state.'))
            rec.periods_ids.unlink()
        return super().unlink()