# -*- coding: utf-8 -*-
from openerp import http

# class L10nZhTwHrPayroll(http.Controller):
#     @http.route('/l10n_zh_tw_hr_payroll/l10n_zh_tw_hr_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_zh_tw_hr_payroll/l10n_zh_tw_hr_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_zh_tw_hr_payroll.listing', {
#             'root': '/l10n_zh_tw_hr_payroll/l10n_zh_tw_hr_payroll',
#             'objects': http.request.env['l10n_zh_tw_hr_payroll.l10n_zh_tw_hr_payroll'].search([]),
#         })

#     @http.route('/l10n_zh_tw_hr_payroll/l10n_zh_tw_hr_payroll/objects/<model("l10n_zh_tw_hr_payroll.l10n_zh_tw_hr_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_zh_tw_hr_payroll.object', {
#             'object': obj
#         })