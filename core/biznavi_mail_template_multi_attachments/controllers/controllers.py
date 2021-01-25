# -*- coding: utf-8 -*-
from odoo import http

# class BiznaviMailTemplateMultiAttachments(http.Controller):
#     @http.route('/biznavi_mail_template_multi_attachments/biznavi_mail_template_multi_attachments/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biznavi_mail_template_multi_attachments/biznavi_mail_template_multi_attachments/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biznavi_mail_template_multi_attachments.listing', {
#             'root': '/biznavi_mail_template_multi_attachments/biznavi_mail_template_multi_attachments',
#             'objects': http.request.env['biznavi_mail_template_multi_attachments.biznavi_mail_template_multi_attachments'].search([]),
#         })

#     @http.route('/biznavi_mail_template_multi_attachments/biznavi_mail_template_multi_attachments/objects/<model("biznavi_mail_template_multi_attachments.biznavi_mail_template_multi_attachments"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biznavi_mail_template_multi_attachments.object', {
#             'object': obj
#         })