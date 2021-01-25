# -*- coding: utf-8 -*-
from odoo import http


# class Tokiku(http.Controller):
#     @http.route('/projects/', type='json', auth='user')
#     def projects(self, **kw):
#         return "Hello, world"

# class Tokiku(http.Controller):
#     @http.route('/tokiku/tokiku/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tokiku/tokiku/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tokiku.listing', {
#             'root': '/tokiku/tokiku',
#             'objects': http.request.env['tokiku.tokiku'].search([]),
#         })

#     @http.route('/tokiku/tokiku/objects/<model("tokiku.tokiku"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tokiku.object', {
#             'object': obj
#         })