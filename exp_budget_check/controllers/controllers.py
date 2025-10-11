# -*- coding: utf-8 -*-
from odoo import http

# class ExpBudgetCheck(http.Controller):
#     @http.route('/exp_budget_check/exp_budget_check/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/exp_budget_check/exp_budget_check/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('exp_budget_check.listing', {
#             'root': '/exp_budget_check/exp_budget_check',
#             'objects': http.request.env['exp_budget_check.exp_budget_check'].search([]),
#         })

#     @http.route('/exp_budget_check/exp_budget_check/objects/<model("exp_budget_check.exp_budget_check"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('exp_budget_check.object', {
#             'object': obj
#         })