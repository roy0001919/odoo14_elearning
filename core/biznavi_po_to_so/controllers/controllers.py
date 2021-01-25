# -*- coding: utf-8 -*-
from odoo import http

# class BiznaviPoToSo(http.Controller):
#     @http.route('/biznavi_po_to_so/biznavi_po_to_so/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_po_to_so/biznavi_po_to_so/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_po_to_so.listing', {
#             'root': '/biznavi_po_to_so/biznavi_po_to_so',
#             'objects': http.request.env['biznavi_po_to_so.biznavi_po_to_so'].search([]),
#         })

#     @http.route('/biznavi_po_to_so/biznavi_po_to_so/objects/<model("biznavi_po_to_so.biznavi_po_to_so"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_po_to_so.object', {
#             'object': obj
#         })