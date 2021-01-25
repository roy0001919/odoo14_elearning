# -*- coding: utf-8 -*-
from openerp import http

# class BaseVatTw(http.Controller):
#     @http.route('/base_vat_tw/base_vat_tw/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_vat_tw/base_vat_tw/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_vat_tw.listing', {
#             'root': '/base_vat_tw/base_vat_tw',
#             'objects': http.request.env['base_vat_tw.base_vat_tw'].search([]),
#         })

#     @http.route('/base_vat_tw/base_vat_tw/objects/<model("base_vat_tw.base_vat_tw"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_vat_tw.object', {
#             'object': obj
#         })