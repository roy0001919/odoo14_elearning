# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import urllib2
import json
from urllib2 import urlopen
from urllib2 import URLError, HTTPError
from openerp.exceptions import UserError

from openerp import models, fields, api, tools, _

_logger = logging.getLogger(__name__)


class MethodRequest(urllib2.Request):
	def __init__(self, *args, **kwargs):
		if 'method' in kwargs:
			self._method = kwargs['method']
			del kwargs['method']
		else:
			self._method = None
		return urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self, *args, **kwargs):
		if self._method is not None:
			return self._method
		return urllib2.Request.get_method(self, *args, **kwargs)


class ObjectView(object):
	def __init__(self, d):
		self.__dict__ = d


class Ddns(models.Model):
	_name = 'biznavi.ddns'

	name = fields.Char(string='Name')
	host = fields.Char(string='Host')
	ip = fields.Char(string='ip')
	ttl = fields.Integer(string='DNS TTL', default=3600)
	godaddy = fields.Many2one('biznavi.ddns.godaddy', string="Godaddy Account", required=True, default=lambda self: self.env['biznavi.ddns.godaddy'].search([('default_account','=',True)]))


	@api.multi
	def act_update_dns(self):

		params = ObjectView({'hostname': self.host, 'ip': self.ip, 'ttl': self.ttl, 'key': self.godaddy.key, 'secret': self.godaddy.secret})

		hostnames = params.hostname.split('.')

		if len(hostnames) < 3:
			msg = _('Hostname "{}" is not a fully-qualified host name of form "HOST.DOMAIN.TOP".').format(params.hostname)
			raise UserError(msg)

		if not params.ip:
			try:
				f = urlopen("http://ipv4.icanhazip.com/")
				resp = f.read()
				params.ip = resp.strip()
				self.ip = params.ip
			except URLError:
				msg = _('Unable to automatically obtain IP address from http://ipv4.icanhazip.com/.')
				raise UserError(msg)

		ips = params.ip.split('.')
		if len(ips) != 4 or \
				not ips[0].isdigit() or not ips[1].isdigit() or not ips[2].isdigit() or not ips[3].isdigit() or \
						int(ips[0]) > 255 or int(ips[1]) > 255 or int(ips[2]) > 255 or int(ips[3]) > 255:
			msg = '"{}" is not valid IP address.'.format(params.ip)
			raise UserError(msg)

		url = 'https://api.godaddy.com/v1/domains/{}/records/A/{}'.format('.'.join(hostnames[1:]), hostnames[0])
		data = json.dumps([{"data": params.ip, "ttl": params.ttl, "name": hostnames[0], "type": "A"}])
		req = MethodRequest(url, method='PUT', data=data)

		req.add_header("Content-Type", "application/json")
		req.add_header("Accept", "application/json")
		if params.key and params.secret:
			req.add_header("Authorization", "sso-key {}:{}".format(params.key, params.secret))

		try:
			f = urlopen(req)
			resp = f.read()
			ret = json.loads(resp)
		except HTTPError as e:
			if e.code == 400:
				msg = _('Unable to set IP address: GoDaddy API URL ({}) was malformed.').format(req.full_url)
			elif e.code == 401:
				if params.key and params.secret:
					msg = _('''Unable to set IP address: --key or --secret option incorrect.
	Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a @ file.''')
				else:
					msg = _('''Unable to set IP address: --key or --secret option missing.
	Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a @ file.''')
			elif e.code == 403:
				msg = _('''Unable to set IP address: customer identified by --key and --secret options denied permission.
	Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a @ file.''')
			elif e.code == 404:
				msg = _('Unable to set IP address: {} not found at GoDaddy.').format(params.hostname)
			elif e.code == 422:
				msg = _('Unable to set IP address: "{}" has invalid domain.').format(params.hostname)
			elif e.code == 429:
				msg = _('Unable to set IP address: too many requests to GoDaddy within brief period.')
			else:
				msg = _('Unable to set IP address: GoDaddy API failure because "{}".').format(e.reason)
			raise UserError(msg)
		except URLError as err:
			msg = _('Unable to set IP address: GoDaddy API failure because "{}".').format(err.reason)
			raise UserError(msg)

		msg = _('IP address for %s set to %s.') % (params.hostname, params.ip)
		ctx = dict(
			default_message=msg,
		)
		return {
			'name': _('DNS Update'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'biznavi.msgbox',
			'target': 'new',
			'context': ctx,
		}


class GoDaddy(models.Model):
	_name = 'biznavi.ddns.godaddy'

	name = fields.Char(string='Account')
	key = fields.Char(string='Key')
	secret = fields.Char(string='Secret')
	default_account = fields.Boolean(string="Default Value")

	@api.multi
	def write(self, vals):
		if vals['default_account'] == True:
			for gd in self.env["biznavi.ddns.godaddy"].search([('id', '!=', self.id)]):
				gd.default_account = False

		return super(GoDaddy, self).write(vals)

