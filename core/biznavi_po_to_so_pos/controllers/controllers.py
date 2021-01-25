# -*- coding: utf-8 -*-
from odoo import http

# class BiznaviPoToSoPos(http.Controller):
#     @http.route('/biznavi_po_to_so_pos/biznavi_po_to_so_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_po_to_so_pos/biznavi_po_to_so_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_po_to_so_pos.listing', {
#             'root': '/biznavi_po_to_so_pos/biznavi_po_to_so_pos',
#             'objects': http.request.env['biznavi_po_to_so_pos.biznavi_po_to_so_pos'].search([]),
#         })

#     @http.route('/biznavi_po_to_so_pos/biznavi_po_to_so_pos/objects/<model("biznavi_po_to_so_pos.biznavi_po_to_so_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_po_to_so_pos.object', {
#             'object': obj
#         })