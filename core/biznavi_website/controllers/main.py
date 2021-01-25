# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz
from odoo import http, tools, _, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


class BizNaviWebsite(http.Controller):

    @http.route('/page/homepage', auth='public', website=True)
    def announcements(self, **kw):

        tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        today = datetime.strftime(datetime.now(tz), '%Y-%m-%d 00:00:00')
        announcements = request.env['biznavi_website.announcement'].sudo().search([('active', '=', True), '|', ('date_from', '=', False),  ('date_from', '<=', today), '|', ('date_to', '=', False), ('date_to', '>=', today)])
        return http.request.render('website.homepage', {
            'announcements': announcements
        })
