# -*- coding: utf-8 -*-
from openerp import http

# class BiznaviAccountInvoiceReport(http.Controller):
#     @http.route('/biznavi_account_invoice_report/biznavi_account_invoice_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_account_invoice_report/biznavi_account_invoice_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_account_invoice_report.listing', {
#             'root': '/biznavi_account_invoice_report/biznavi_account_invoice_report',
#             'objects': http.request.env['biznavi_account_invoice_report.biznavi_account_invoice_report'].search([]),
#         })

#     @http.route('/biznavi_account_invoice_report/biznavi_account_invoice_report/objects/<model("biznavi_account_invoice_report.biznavi_account_invoice_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_account_invoice_report.object', {
#             'object': obj
#         })