# -*- coding: utf-8 -*-
from odoo import http

# class BiznaviOrderSync(http.Controller):
#     @http.route('/biznavi_order_sync/biznavi_order_sync/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_order_sync/biznavi_order_sync/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_order_sync.listing', {
#             'root': '/biznavi_order_sync/biznavi_order_sync',
#             'objects': http.request.env['biznavi_order_sync.biznavi_order_sync'].search([]),
#         })

#     @http.route('/biznavi_order_sync/biznavi_order_sync/objects/<model("biznavi_order_sync.biznavi_order_sync"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_order_sync.object', {
#             'object': obj
#         })