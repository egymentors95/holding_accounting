# -*- coding: utf-8 -*-
# from odoo import http


# class ReprotPointOfSale(http.Controller):
#     @http.route('/reprot_point_of_sale/reprot_point_of_sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reprot_point_of_sale/reprot_point_of_sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('reprot_point_of_sale.listing', {
#             'root': '/reprot_point_of_sale/reprot_point_of_sale',
#             'objects': http.request.env['reprot_point_of_sale.reprot_point_of_sale'].search([]),
#         })

#     @http.route('/reprot_point_of_sale/reprot_point_of_sale/objects/<model("reprot_point_of_sale.reprot_point_of_sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reprot_point_of_sale.object', {
#             'object': obj
#         })
