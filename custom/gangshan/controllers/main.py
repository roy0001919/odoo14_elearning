# -*- coding: utf-8 -*-
import logging
import re
from odoo import http, SUPERUSER_ID, _
from odoo.http import request
import pytz

from odoo import fields

from core.website_booking_calendar.controllers.main import WebsiteBookingCalendar

_logger = logging.getLogger(__name__)


class WebsiteBookingCalendar(WebsiteBookingCalendar):

    @http.route('/booking/calendar/confirm', type='http', auth='public', website=True, csrf=False)
    def order(self, **kwargs):
        tz = int(kwargs.get('timezone', '0'))
        product_id = None
        lines = {}
        for key, arg in kwargs.iteritems():
            # print "key: %s value: %s" % (key, arg)
            if key.startswith('product_id'):
                m = re.match(
                    '^product_id\[(\d+)\]\[([\d-]+ [\d:]+)\-([\d-]+ [\d:]+)\]\[(\d+)\]$', key)
                resource_id = m.group(1)
                start = m.group(2)
                end = m.group(3)
                batch = m.group(4)
                product_id = arg

            if key.startswith('add_qty'):
                add_qty = re.match('^add_qty\-(\d+)\-(\d+)', key)
                lines[add_qty.group(2)] = arg
            if key == 'contact_usr':
                contact_usr = arg
            if key == 'contact_tel':
                contact_tel = arg

        if product_id and len(lines) > 0:
            request.website.sale_reset()

            order = request.website.sale_get_order()
            if order and order.state in ['draft', 'cancel']:
                order.unlink()

            # user_tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
            # booking_start = user_tz.localize(fields.Datetime.from_string(start)).astimezone(pytz.utc).date()
            booking_start = fields.Datetime.from_string(start).date()
            # _logger.info('start:%s' % booking_start)
            promo_pricelst = request.env['product.pricelist'].sudo().search([('ticket_promote_end', '!=', False), '|', ('ticket_promote_start', '=', False), ('ticket_promote_start', '<=', booking_start), ('ticket_promote_end', '>=', booking_start)], limit=1)

            if promo_pricelst:
                # _logger.info('code:%s' % promo_pricelst.code)
                order = request.website.sale_get_order(force_create=1, force_pricelist=promo_pricelst.id)
            else:
                # _logger.info('no promo_pricelst')
                order = request.website.sale_get_order(force_create=1)

            if order.state in ['draft', 'cancel']:
                for line in order.order_line:
                    line.unlink()
            for p in lines:
                if int(lines[p]) > 0:
                    order._add_booking_line(int(p), int(resource_id), start, end, tz, lines[p], None, batch,
                                        contact_usr, contact_tel)
            remain_qty = 0
            qty = 0
            for l in order.order_line:
                qty += l.product_uom_qty
                remain_qty = l.get_slot_remain_qty()
                pid = l.product_id.product_tmpl_id.id
            if qty > remain_qty:
                request.website.sale_reset()
                order.state = 'cancel'
                return request.redirect("/shop/product/%s?s=%s" % (pid, int(qty)))

            # order._add_booking_line(int(product_id), int(resource_id), start, end, tz, add_qty, None, batch,
            #                         contact_usr, contact_tel)
            return request.redirect("/shop/cart")
        else:
            request.website.sale_reset()
            return request.redirect("/")

