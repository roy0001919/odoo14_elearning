#-*- coding: utf-8 -*-
import xmlrpclib
import logging
from datetime import datetime, timedelta
import time
import base64
import functools
import imghdr
from cStringIO import StringIO
import openerp
import openerp.modules.registry
from openerp.modules import get_resource_path
from openerp import http
from openerp.http import request
_logger = logging.getLogger(__name__)
db_monodb = http.db_monodb


class BizNaviBinary(openerp.addons.web.controllers.main.Binary):
	@http.route([
		'/web/binary/company_logo',
		'/logo',
		'/logo.png',
	], type='http', auth="none", cors="*", website=True)
	def company_logo(self,dbname=None, **kw):
		imgname = 'logo'
		imgext = '.png'
		placeholder = functools.partial(get_resource_path, 'biznavi', 'static', 'src', 'img')
		uid = None
		if request.session.db:
			dbname = request.session.db
			uid = request.session.uid
		elif dbname is None:
			dbname = db_monodb()

		if not uid:
			uid = openerp.SUPERUSER_ID

		if not dbname:
			response = http.send_file(placeholder(imgname + imgext))
		else:
			try:
				# create an empty registry
				registry = openerp.modules.registry.Registry(dbname)
				with registry.cursor() as cr:
					cr.execute("""SELECT c.logo_web, c.write_date
									FROM res_users u
							   LEFT JOIN res_company c
									  ON c.id = u.company_id
								   WHERE u.id = %s
							   """, (uid,))
					row = cr.fetchone()
					if row and row[0]:
						image_base64 = str(row[0]).decode('base64')
						image_data = StringIO(image_base64)
						imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
						response = http.send_file(image_data, filename=imgname + imgext, mtime=row[1])
					else:
						response = http.send_file(placeholder('nologo.png'))
			except Exception:
				response = http.send_file(placeholder(imgname + imgext))

		return response


class BiznaviController(http.Controller):
	# request  ====> {"params": {"db":"neweb", "username":"admin", "password":"Admin1234!@#$"}}
	@http.route('/biznavi/login', auth='public', type='json', methods=['POST'])
	def login(self, **post):
		db, usr, pwd = post.get('db'),post.get('username'),post.get('password')
		url = http.request.env['ir.config_parameter'].get_param('web.base.url')
		common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
		uid = common.authenticate(db, usr, pwd, {})
		now = datetime.now()
		expdt = now + timedelta(minutes=30)
		exp_str = hex(int(time.mktime(expdt.timetuple())))[2:]
		exp_str = exp_str.replace('L', '')
		sessid = base64.b64encode('%s:%s:%s' % (exp_str, uid, db))
		recoveryid = base64.b64decode(sessid)
		return {'session_id': sessid}
