# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.http import request
from itertools import groupby
from operator import itemgetter 


class BudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    @api.model
    def hierarchical_chart_details(self,model):
        """
        returning a sorted list of budget lines parented
        to analytic accounts.
        """
        uid = request.session.uid
        user = self.env['res.users'].sudo().browse(uid)
        budget_lines = self.env['crossovered.budget.lines'].sudo().search([])
        sorted_lines = budget_lines.sorted(key=lambda x:x.analytic_account_id.id)
        analytics = []
        lines = []
        for key,values in groupby(sorted_lines,key = lambda x: x.analytic_account_id.id):
            analytic = {}
            analytic['planned_amount'] = 0.0
            analytic['theoritical_amount'] = 0.0
            analytic['practical_amount'] = 0.0
            analytic['percentage'] = 0.0
            if key != False:
                analytic['id'] = str(key) + 'a'
            else:
                analytic['id'] = False
            for value in values:
                line = {}
                analytic['planned_amount'] += value.planned_amount
                line['planned_amount'] = value.planned_amount
                analytic['percentage'] += value.percentage
                line['percentage'] = value.percentage
                analytic['practical_amount'] += value.practical_amount
                line['practical_amount'] = value.practical_amount
                analytic['theoritical_amount'] += value.theoritical_amount
                line['theoritical_amount'] = value.theoritical_amount
                analytic['_name'] = 'account.account'
                analytic['name'] = value.analytic_account_id.name or 'Undefined'
                line['name'] = value.general_budget_id.name or 'Undefined'
                line['_name'] = 'budget_lines'
                if analytic['id'] != False:
                    line['parent_id'] = (analytic['id'] , 'a')
                line['id'] = str(value.id) +'b' 
                lines.append(line)
                line = {}
            if analytic['name'] != False:
                analytics.append(analytic)

        data = lines + analytics 

        for rec in data:
            if 'parent_id' not in rec:
                rec['parent_id'] = False
            if rec['parent_id'] and rec['parent_id'][0] == False:
                rec['parent_id'] = False
            if 'code' in rec and rec['code'] == False:
                rec['code'] = '-'
            rec['planned_amount'] = str("{:,.2f}".format(round(rec['planned_amount'],2)))
            rec['percentage'] = str("{:,.2f}".format(round(rec['percentage'],2)))
            rec['practical_amount'] = str("{:,.2f}".format(round(rec['practical_amount'],2)))
            rec['theoritical_amount'] = str("{:,.2f}".format(round(rec['theoritical_amount'],2)))
            
        all_data = []
        groupby_dicts = {}
        for rec in data:
            key = rec['parent_id'] and rec['parent_id'][0] or False
            value = rec

            if key:
                groupby_dicts[key] = groupby_dicts.get(key, [])
                groupby_dicts[key].append(value)
            elif not key:
                all_data.append(value)

        computed_parents = [False]
        while len(computed_parents) != len(groupby_dicts.keys()) + 1:
            for k in groupby_dicts:
                if k in computed_parents:
                    continue
                v = list(groupby_dicts[k])
                if all_data:
                    for rec in all_data:
                        if rec['id'] == k:
                            all_data = all_data[:all_data.index(
                                rec)] + list(v)[::-1] + \
                                all_data[all_data.index(rec):]

                            computed_parents.append(k)
                if not all_data:
                    all_data = list(v)

        all_data = all_data[::-1]
        return all_data
