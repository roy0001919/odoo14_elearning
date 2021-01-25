# -*- coding: utf-8 -*-
from openerp import http

# class BiznaviHrHolidaysExpired(http.Controller):
#     @http.route('/biznavi_hr_holidays_expired/biznavi_hr_holidays_expired/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_hr_holidays_expired/biznavi_hr_holidays_expired/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_hr_holidays_expired.listing', {
#             'root': '/biznavi_hr_holidays_expired/biznavi_hr_holidays_expired',
#             'objects': http.request.env['biznavi_hr_holidays_expired.biznavi_hr_holidays_expired'].search([]),
#         })

#     @http.route('/biznavi_hr_holidays_expired/biznavi_hr_holidays_expired/objects/<model("biznavi_hr_holidays_expired.biznavi_hr_holidays_expired"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_hr_holidays_expired.object', {
#             'object': obj
#         })