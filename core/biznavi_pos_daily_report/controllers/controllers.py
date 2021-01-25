# -*- coding: utf-8 -*-
from odoo import http

# class BiznaviPosDailyReport(http.Controller):
#     @http.route('/biznavi_pos_daily_report/biznavi_pos_daily_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_pos_daily_report/biznavi_pos_daily_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_pos_daily_report.listing', {
#             'root': '/biznavi_pos_daily_report/biznavi_pos_daily_report',
#             'objects': http.request.env['biznavi_pos_daily_report.biznavi_pos_daily_report'].search([]),
#         })

#     @http.route('/biznavi_pos_daily_report/biznavi_pos_daily_report/objects/<model("biznavi_pos_daily_report.biznavi_pos_daily_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_pos_daily_report.object', {
#             'object': obj
#         })