# -*- coding: utf-8 -*-
from odoo import http

# class PaymentIbon(http.Controller):
#     @http.route('/payment_ibon/payment_ibon/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payment_ibon/payment_ibon/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('payment_ibon.listing', {
#             'root': '/payment_ibon/payment_ibon',
#             'objects': http.request.env['payment_ibon.payment_ibon'].search([]),
#         })

#     @http.route('/payment_ibon/payment_ibon/objects/<model("payment_ibon.payment_ibon"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payment_ibon.object', {
#             'object': obj
#         })