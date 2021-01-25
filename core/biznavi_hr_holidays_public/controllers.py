# -*- coding: utf-8 -*-
from openerp import http

# class HrPublicHolidays(http.Controller):
#     @http.route('/hr_public_holidays/hr_public_holidays/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_public_holidays/hr_public_holidays/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_public_holidays.listing', {
#             'root': '/hr_public_holidays/hr_public_holidays',
#             'objects': http.request.env['hr_public_holidays.hr_public_holidays'].search([]),
#         })

#     @http.route('/hr_public_holidays/hr_public_holidays/objects/<model("hr_public_holidays.hr_public_holidays"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_public_holidays.object', {
#             'object': obj
#         })