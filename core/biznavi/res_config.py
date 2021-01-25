from openerp import _
from openerp import fields, models, api
from subprocess import Popen, PIPE, call
from openerp.exceptions import UserError
import openerp
import logging
import os
import netifaces
import hashlib
import base64
from datetime import datetime
import time
from openerp import http
import openerp.addons.web_settings_dashboard.controllers.main as main

_logger = logging.getLogger(__name__)

valid_content = """<?xml version="1.0"?>\r\n\t\t<t t-name="web.menu_secondary">\r\n            <a class="oe_logo" t-att-href="''/web/?debug'' if debug else ''/web''">\r\n                <span class="oe_logo_edit">Edit Company data</span>\r\n                <img src="/web/binary/company_logo"/> \r\n            </a>\r\n            <div class="oe_secondary_menus_container">\r\n                <t t-foreach="menu_data[''children'']" t-as="menu">\r\n                    <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[''id'']">\r\n                        <t t-foreach="menu[\''children'']" t-as="menu">\r\n                            <div class="oe_secondary_menu_section">                                \r\n                                <t t-if="menu[''children'']"><t t-esc="menu[''name'']"/></t>\r\n                                <t t-if="not menu[''children'']"><t t-call="web.menu_link"/></t>\r\n                            </div>\r\n                            <t t-call="web.menu_secondary_submenu"/>\r\n                        </t>\r\n                    </div>\r\n                </t>\r\n            </div>\r\n            <div class="oe_footer">\r\n                BizNavi@<a href="https://www.cenoq.com" target="_blank"><span>CENOQ</span></a>\r\n            </div>\r\n        </t>"""
invalid_content = """<?xml version="1.0"?>\r\n\t\t<t t-name="web.menu_secondary">\r\n            <a class="oe_logo" t-att-href="''/web/?debug'' if debug else ''/web''">\r\n                <span class="oe_logo_edit">Edit Company data</span>\r\n                <img src="/web/binary/company_logo"/> \r\n            </a>\r\n            <label style="color:red;font-weight:bold;text-align:center;background:rgba(37, 37, 37, 0.8);line-height:25px;margin-top: -60px;margin-bottom:30px;transform:rotate(-9deg);">Illigal Copy of BizNavi</label>\r\n            <script>function timeout(){alert("You are using an illigal copy of BizNavi or with invaild subscription. Please contact your reseller for further assistance.");setTimeout("timeout()",30000);}timeout();</script>\r\n            <div class="oe_secondary_menus_container">\r\n                <t t-foreach="menu_data[''children'']" t-as="menu">\r\n                    <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[''id'']">\r\n                        <t t-foreach="menu[\''children'']" t-as="menu">\r\n                            <div class="oe_secondary_menu_section">                                \r\n                                <t t-if="menu[''children'']"><t t-esc="menu[''name'']"/></t>\r\n                                <t t-if="not menu[''children'']"><t t-call="web.menu_link"/></t>\r\n                            </div>\r\n                            <t t-call="web.menu_secondary_submenu"/>\r\n                        </t>\r\n                    </div>\r\n                </t>\r\n            </div>\r\n            <div class="oe_footer">\r\n                BizNavi@<a href="http://www.cenoq.com" target="_blank"><span>CENOQ</span></a>\r\n            </div>\r\n        </t>"""
expired_content = """<?xml version="1.0"?>\r\n\t\t<t t-name="web.menu_secondary">\r\n            <a class="oe_logo" t-att-href="''/web/?debug'' if debug else ''/web''">\r\n                <span class="oe_logo_edit">Edit Company data</span>\r\n                <img src="/web/binary/company_logo"/> \r\n            </a>\r\n            <label style="color:red;font-weight:bold;text-align:center;background:#f0de89;line-height:25px;margin-top: -30px;">Subscription Expired</label>\r\n            <div class="oe_secondary_menus_container">\r\n                <t t-foreach="menu_data[''children'']" t-as="menu">\r\n                    <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[''id'']">\r\n                        <t t-foreach="menu[\''children'']" t-as="menu">\r\n                            <div class="oe_secondary_menu_section">                                \r\n                                <t t-if="menu[''children'']"><t t-esc="menu[''name'']"/></t>\r\n                                <t t-if="not menu[''children'']"><t t-call="web.menu_link"/></t>\r\n                            </div>\r\n                            <t t-call="web.menu_secondary_submenu"/>\r\n                        </t>\r\n                    </div>\r\n                </t>\r\n            </div>\r\n            <div class="oe_footer">\r\n                BizNavi@<a href="http://www.cenoq.com" target="_blank"><span>CENOQ</span></a>\r\n            </div>\r\n        </t>"""
trial_content = """<?xml version="1.0"?>\r\n\t\t<t t-name="web.menu_secondary">\r\n            <a class="oe_logo" t-att-href="''/web/?debug'' if debug else ''/web''">\r\n                <span class="oe_logo_edit">Edit Company data</span>\r\n                <img src="/web/binary/company_logo"/> \r\n            </a>\r\n            <label style="color:white;font-weight:bold;text-align:center;background:rgba(23,89,175, 0.3);line-height:25px;margin-top: -30px;">Trial Version</label>\r\n            <div class="oe_secondary_menus_container">\r\n                <t t-foreach="menu_data[''children'']" t-as="menu">\r\n                    <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[''id'']">\r\n                        <t t-foreach="menu[\''children'']" t-as="menu">\r\n                            <div class="oe_secondary_menu_section">                                \r\n                                <t t-if="menu[''children'']"><t t-esc="menu[''name'']"/></t>\r\n                                <t t-if="not menu[''children'']"><t t-call="web.menu_link"/></t>\r\n                            </div>\r\n                            <t t-call="web.menu_secondary_submenu"/>\r\n                        </t>\r\n                    </div>\r\n                </t>\r\n            </div>\r\n            <div class="oe_footer">\r\n                BizNavi@<a href="http://www.cenoq.com" target="_blank"><span>CENOQ</span></a>\r\n            </div>\r\n        </t>"""
exp_trial_content = """<?xml version="1.0"?>\r\n\t\t<t t-name="web.menu_secondary">\r\n            <a class="oe_logo" t-att-href="''/web/?debug'' if debug else ''/web''">\r\n                <span class="oe_logo_edit">Edit Company data</span>\r\n                <img src="/web/binary/company_logo"/> \r\n            </a>\r\n            <label style="color:red;font-weight:bold;text-align:center;background:rgba(37, 37, 37, 0.8);line-height:25px;margin-top: -60px;margin-bottom:30px;transform:rotate(-9deg);">Trial Expired</label>\r\n            <script>function timeout(){alert("Trial Expired!!! Please contact your reseller for further assistance.");setTimeout("timeout()",30000);}timeout();</script>\r\n            <div class="oe_secondary_menus_container">\r\n                <t t-foreach="menu_data[''children'']" t-as="menu">\r\n                    <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[''id'']">\r\n                        <t t-foreach="menu[\''children'']" t-as="menu">\r\n                            <div class="oe_secondary_menu_section">                                \r\n                                <t t-if="menu[''children'']"><t t-esc="menu[''name'']"/></t>\r\n                                <t t-if="not menu[''children'']"><t t-call="web.menu_link"/></t>\r\n                            </div>\r\n                            <t t-call="web.menu_secondary_submenu"/>\r\n                        </t>\r\n                    </div>\r\n                </t>\r\n            </div>\r\n            <div class="oe_footer">\r\n                BizNavi@<a href="http://www.cenoq.com" target="_blank"><span>CENOQ</span></a>\r\n            </div>\r\n        </t>"""


class Biznavi(models.TransientModel):
	_inherit = "res.config.settings"
	_name = "biznavi.config.settings"
	_description = "BizNavi Config"
	_defaults = {
		'biznavi_theme': 'base',
	}

	# Base
	module_biznavi_base_vat = fields.Boolean('Enable Taiwan VAT number rule',
			help ="""Install Taiwan VAT Number rule""")

	# Accounting
	module_l10n_tw = fields.Boolean('Taiwan Accounting Package',
			help ="""Install Taiwan Accounting Package""")
	module_biznavi_account_invoice_report = fields.Boolean('Taiwan Computer Invoice',
			help ="""Install Taiwan Computer Invoice Report""")
	module_biznavi_invoice_merge = fields.Boolean('Add invoice merge Feature',
			help ="""Add invoice merge Feature""")

	# HR
	module_biznavi_hr_holidays_public = fields.Boolean('public holidays feature',
			help ="""Install public holidays feature""")
	module_biznavi_hr_holidays_expired = fields.Boolean('Holidays auto expired feature',
			help ="""Install holidays auto expired feature""")
	module_biznavi_hr_payroll = fields.Boolean('Taiwanese payroll calculation feature',
			help ="""Install Taiwanese payroll calculation feature""")

	updated = fields.Integer('Number of modules updated', readonly=True)
	added = fields.Integer('Number of modules added', readonly=True)
	state = fields.Selection([('init', 'init'), ('done', 'done')], 'Status', readonly=True, default='init')

	biznavi_theme = fields.Selection([('base', 'base'), ('blue', 'blue')], 'Theme')

	server_id = fields.Text('Server ID')
	exp_date = fields.Char('Expired Date')
	key = fields.Text('Key')

	@api.model
	def get_default_key_values(self, fields):
		conf = self.env['ir.config_parameter']
		return {
			'key': conf.get_param('biznavi.key'),
			'exp_date': conf.get_param('biznavi.exp_date'),
		}

	@api.one
	def set_key_values(self):
		conf = self.env['ir.config_parameter']
		if not self.key:
			self.key = ""
		conf.set_param('biznavi.key', self.key)
		conf.set_param('biznavi.exp_date', self.exp_date)

	@api.one
	def update_module(self):
		self.updated, self.added = self.env['ir.module.module'].update_list()
		self.state = 'done'
		return False

	@api.multi
	def act_update(self):
		Popen(['git', 'remote', 'update'])
		cur_dir = os.path.dirname(os.path.realpath(__file__)).replace('addons/biznavi','')
		process = Popen(['git','pull'], stdout=PIPE, stderr=PIPE, cwd=cur_dir)
		git_pull, err = process.communicate()
		_logger.info('msg: %s ' % git_pull)
		_logger.info('err: %s ' % err)
		msg = _('BizNavi update failed!')
		if 'up-to-date' in git_pull:
			msg = _('Already up-to-date')
		else:
			for line in git_pull.split("\n"):
				if 'changed,' in line or '(+),' in line or '(-)' in line:
					msg = 'Updated: ' + line
					ir_module = self.env['ir.module.module']
					cr = self.env.cr
					ids = ir_module.search([('state', 'in', ['to upgrade', 'to install'])])
					if ids:
						cr.execute("""SELECT d.name FROM ir_module_module m
													JOIN ir_module_module_dependency d ON (m.id = d.module_id)
													LEFT JOIN ir_module_module m2 ON (d.name = m2.name)
									  WHERE m.id in %s and (m2.state IS NULL or m2.state IN %s)""", (tuple(ids), ('uninstalled',)))
						unmet_packages = [x[0] for x in cr.fetchall()]
						if unmet_packages:
							raise UserError(_('Following modules are not installed or unknown: %s') % ('\n\n' + '\n'.join(unmet_packages)))
							ir_module.download(cr, uid, ids, context=context)
							cr.commit()
					openerp.api.Environment.reset()
					openerp.modules.registry.RegistryManager.new(cr.dbname, update_module=True)

					#self.update_module()
					Popen(['sudo', 'systemctl','restart' , 'biznavi'])
					break
		ctx = dict(
			default_message=msg,
		)
		return {
			'name': _('BizNavi Update'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.update',
			'target': 'new',
			'context': ctx,
		}

	@api.multi
	def act_writeback_translation(self):
		return {
			'name': _('BizNavi Translation Writeback'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.translation_writeback_wizard',
			'target': 'new'
		}

	@api.multi
	def act_push(self):
		cur_dir = os.path.dirname(os.path.realpath(__file__)).replace('addons/biznavi','')
		process_commit = Popen(['git','commit', '-am', 'From Client Biznavi System'], stdout=PIPE, stderr=PIPE, cwd=cur_dir)
		git_push, err = process_commit.communicate()
		_logger.info('msg: %s ' % git_push)
		_logger.info('err: %s ' % err)
		process = Popen(['git','push'], stdout=PIPE, stderr=PIPE, cwd=cur_dir)
		git_push, err = process.communicate()
		_logger.info('msg: %s ' % git_push)
		_logger.info('err: %s ' % err)
		msg = _('Push Finished!')
		ctx = dict(
			default_message=msg,
		)
		return {
			'name': _('BizNavi Upload'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.update',
			'target': 'new',
			'context': ctx,
		}

	@api.multi
	def act_clean_translation(self):
		cr = self.env.cr
		cr.execute("delete from ir_translation where lang = 'zh_TW' and (src = value or value is null or value = '')")
		msg = _('Translation Cleaned!')
		ctx = dict(
			default_message=msg,
		)
		return {
			'name': _('BizNavi Upload'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.update',
			'target': 'new',
			'context': ctx,
		}

	@api.model
	def get_server_id(self):
		ret_int = 0
		aid_int = 0

		print "get_server_id..."
		for inet in netifaces.interfaces():
			try:
				mac = netifaces.ifaddresses(inet)[netifaces.AF_LINK][0]['addr']
			except KeyError:
				mac = None

			if mac:
				aid_int += 1
				mac_int = int(mac.replace(':', ''), 16)
				ret_int += mac_int
		ret_int += 86640082
		server_id = "%s-%s-%d" % (str(ret_int)[:4], str(ret_int)[4:], aid_int * 8)
		print "server_id: %s " % server_id

		return server_id

	# @api.multi
	# def execute(self):
	# 	if int(time.mktime(datetime.now().timetuple())) > 1471950733:
	# 		try:
	# 			key_code = base64.b64decode(self.key)
	# 		except:
	# 			key_code = False
	# 		if key_code:
	# 			try:
	# 				self.exp_date = datetime.fromtimestamp(int(key_code[:10], 16) / 77).date()
	# 			except:
	# 				self.exp_date = ""
	# 			trial = False
	# 			try:
	# 				if key_code[10:] == '440baf7072c152052c77e54eb994353c916e978aea53942808a8c2a1f2b3a1232f0b9052b413232693ced0ac4c2b3b897b640011453716b9ad7ff0ea315879ea':
	# 					valid = True
	# 					trial = True
	# 				else:
	# 					valid = (key_code[10:] == hashlib.sha512(self.server_id + "2800BizNavi@CENOQ4668").hexdigest())
	# 			except:
	# 				valid = False
	# 			if valid:
	# 				if int(time.mktime(datetime.now().timetuple())) > (int(key_code[:10], 16) / 77):
	# 					if trial:
	# 						self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % exp_trial_content)
	# 					else:
	# 						self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % expired_content)
	# 				else:
	# 					if trial:
	# 						self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % trial_content)
	# 					else:
	# 						self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % valid_content)
	# 			else:
	# 				self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % invalid_content)
	# 		else:
	# 				self.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % invalid_content)
	#
	# 	res = super(Biznavi, self).execute()
	# 	return res
	#
	# _defaults = {
	# 	'server_id': get_server_id,
	# }

	@api.multi
	def act_reset_charts(self):
		company = self.env['res.users'].browse(self.env.uid).company_id
		company.reset_chart()
		_logger.info('Account Chart Reseted for %s' % company.name)

		msg = _('Account Chart Reseted for %s' % company.name)
		ctx = dict(
			default_message=msg,
		)
		return {
			'name': _('Account Chart Reset'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.msgbox',
			'target': 'new',
			'context': ctx,
		}


class WebSettingsDashboard(main.WebSettingsDashboard):

	@staticmethod
	def check_key(key):
		if int(time.mktime(datetime.now().timetuple())) > 1471950733:
			try:
				key_code = base64.b64decode(key)
			except:
				key_code = False
			if key_code:
				trial = False
				try:
					if key_code[10:] == '440baf7072c152052c77e54eb994353c916e978aea53942808a8c2a1f2b3a1232f0b9052b413232693ced0ac4c2b3b897b640011453716b9ad7ff0ea315879ea':
						valid = True
						trial = True
					else:
						valid = (key_code[10:] == hashlib.sha512(WebSettingsDashboard.get_server_id() + "2800BizNavi@CENOQ4668").hexdigest())
				except:
					valid = False
				if valid:
					if int(time.mktime(datetime.now().timetuple())) > (int(key_code[:10], 16) / 77):
						if trial:
							http.request.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % exp_trial_content)
						else:
							http.request.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % expired_content)
					elif trial:
							http.request.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % trial_content)
				else:
					http.request.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % invalid_content)
			else:
				http.request.env.cr.execute("""update ir_ui_view set arch_db = '%s' where name = 'web.menu_secondary'""" % invalid_content)

	@staticmethod
	def get_server_id():
		ret_int = 0
		aid_int = 0
		for inet in netifaces.interfaces():
			try:
				mac = netifaces.ifaddresses(inet)[netifaces.AF_LINK][0]['addr']
			except KeyError:
				mac = None

			if mac:
				aid_int += 1
				mac_int = int(mac.replace(':', ''), 16)
				ret_int += mac_int
		ret_int += 86640082
		server_id = "%s-%s-%d" % (str(ret_int)[:4], str(ret_int)[4:], aid_int * 8)

		return server_id

	@http.route('/web_settings_dashboard/data', type='json', auth='user')
	def web_settings_dashboard_data(self, **kw):
		key = http.request.env['ir.config_parameter'].get_param('biznavi.key')
		# self.check_key(key)
		return super(WebSettingsDashboard, self).web_settings_dashboard_data(**kw)
