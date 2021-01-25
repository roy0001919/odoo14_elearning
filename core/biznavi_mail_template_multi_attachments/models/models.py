# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo import report as odoo_report
import base64

import logging

_logger = logging.getLogger(__name__)


class MailTemplateDetail(models.Model):
	_name = "mail.template.detail"

	report_name = fields.Char('Report Filenames')
	report_template = fields.Many2one('ir.actions.report.xml', 'Report to print and attach')

	template_id = fields.Many2one('mail.template', 'Template')


class MailTemplate(models.Model):
	_inherit = "mail.template"

	template_detail_ids = fields.One2many('mail.template.detail', 'template_id', 'Reports')

	@api.model
	def generate_email(self, res_ids, fields=None):
		_logger.info('inherit method call~')
		self.ensure_one()
		multi_mode = True
		if isinstance(res_ids, (int, long)):
			res_ids = [res_ids]
			multi_mode = False
		if fields is None:
			fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date']

		res_ids_to_templates = self.get_email_template(res_ids)

		# templates: res_id -> template; template -> res_ids
		templates_to_res_ids = {}
		for res_id, template in res_ids_to_templates.iteritems():
			templates_to_res_ids.setdefault(template, []).append(res_id)

		results = dict()
		for template, template_res_ids in templates_to_res_ids.iteritems():
			Template = self.env['mail.template']
			# generate fields value for all res_ids linked to the current template
			if template.lang:
				Template = Template.with_context(lang=template._context.get('lang'))
			for field in fields:
				Template = Template.with_context(safe=field in {'subject'})
				generated_field_values = Template.render_template(
					getattr(template, field), template.model, template_res_ids,
					post_process=(field == 'body_html'))
				for res_id, field_value in generated_field_values.iteritems():
					results.setdefault(res_id, dict())[field] = field_value
			# compute recipients
			if any(field in fields for field in ['email_to', 'partner_to', 'email_cc']):
				results = template.generate_recipients(results, template_res_ids)
			# update values for all res_ids
			for res_id in template_res_ids:
				values = results[res_id]
				# body: add user signature, sanitize
				if 'body_html' in fields and template.user_signature:
					signature = self.env.user.signature
					if signature:
						values['body_html'] = tools.append_content_to_html(values['body_html'], signature,
						                                                   plaintext=False)
				if values.get('body_html'):
					values['body'] = tools.html_sanitize(values['body_html'])
				# technical settings
				values.update(
					mail_server_id=template.mail_server_id.id or False,
					auto_delete=template.auto_delete,
					model=template.model,
					res_id=res_id or False,
					attachment_ids=[attach.id for attach in template.attachment_ids],
				)

			# Add report in attachments: generate once for all template_res_ids
			if template.report_template:
				for res_id in template_res_ids:
					attachments = []
					report_name = self.render_template(template.report_name, template.model, res_id)
					report = template.report_template
					report_service = report.report_name

					if report.report_type in ['qweb-html', 'qweb-pdf']:
						result, format = Template.env['report'].get_pdf([res_id], report_service), 'pdf'
					else:
						result, format = odoo_report.render_report(self._cr, self._uid, [res_id], report_service,
						                                           {'model': template.model}, Template._context)

					# TODO in trunk, change return format to binary to match message_post expected format
					result = base64.b64encode(result)
					if not report_name:
						report_name = 'report.' + report_service
					ext = "." + format
					if not report_name.endswith(ext):
						report_name += ext
					attachments.append((report_name, result))

					for tmp_detail in template.template_detail_ids:
						report_name1 = self.render_template(tmp_detail.report_name, template.model, res_id)
						report1 = tmp_detail.report_template
						report_service1 = report1.report_name

						if report1.report_type in ['qweb-html', 'qweb-pdf']:
							result1, format1 = Template.env['report'].get_pdf([res_id], report_service1), 'pdf'
						else:
							result1, format1 = odoo_report.render_report(self._cr, self._uid, [res_id], report_service1,
							                                           {'model': template.model}, Template._context)

						result1 = base64.b64encode(result1)
						if not report_name1:
							report_name1 = 'report.' + report_service1
						ext = "." + format
						if not report_name1.endswith(ext):
							report_name1 += ext
						attachments.append((report_name1, result1))


					results[res_id]['attachments'] = attachments

		return multi_mode and results or results[res_ids[0]]

