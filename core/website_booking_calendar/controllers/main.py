# -*- coding: utf-8 -*-
import json
import logging
import re
import urllib
import urllib2
import requests
import simplejson
import pytz
from openerp import http, SUPERUSER_ID, _
from openerp.http import request
from datetime import datetime
from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteBookingCalendar(http.Controller):

    def _get_resources(self, params):
        cr, uid, context = request.cr, request.uid, request.context
        resource_obj = request.env['resource.resource'].sudo()
        domain = [('to_calendar', '=', True)]
        resource_ids = resource_obj.search(
            cr, SUPERUSER_ID, domain, context=context)
        resources = resource_obj.browse(
            cr, SUPERUSER_ID, resource_ids, context=context)
        return resources

    def _get_values(self, params):
        values = {
            'resources': self._get_resources(params)
        }
        return values

    def checkout_redirection(self, order):
        # must have a draft sale order with lines at this point, otherwise reset
        if not order or order.state != 'draft':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        # if transaction pending / done: redirect to confirmation
        tx = request.env.context.get('website_sale_transaction')
        if tx and tx.state != 'draft':
            return request.redirect('/shop/payment/confirmation/%s' % order.id)

    @http.route(['/booking/calendar'], type='http', auth="public", website=True)
    def calendar(self, **kwargs):
        return request.website.render('website_booking_calendar.index', self._get_values(kwargs))

    @http.route('/booking/calendar/confirm/form', type='http', auth='public', website=True)
    def confirm_form(self, **kwargs):
        events = simplejson.loads(kwargs['events'])
        cr, uid, context = request.cr, request.uid, request.context
        bookings = request.env[
            "sale.order.line"].sudo().events_to_bookings(events)
        return request.website.render('website_booking_calendar.confirm_form', {
            'bookings': bookings
        })

    @http.route('/booking/calendar/confirm', type='http', auth='public', website=True, csrf=False)
    def order(self, **kwargs):
        tz = int(kwargs.get('timezone', '0'))
        product_id = None
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
            if key == 'add_qty':
                add_qty = arg
            if key == 'contact_usr':
                contact_usr = arg
            if key == 'contact_tel':
                contact_tel = arg

        if product_id:
            request.website.sale_reset()
            order = request.website.sale_get_order(force_create=1)
            if order.state in ['draft', 'cancel']:
                for line in order.order_line:
                    line.unlink()
            order._add_booking_line(int(product_id), int(resource_id), start, end, tz, add_qty, None, batch, contact_usr, contact_tel)
            return request.redirect("/shop/cart")
        else:
            request.website.sale_reset()
            return request.redirect("/")

    @http.route('/booking/product/<int:product_id>', type='http', auth='public', website=True)
    def get_product_page(self, product_id, **kwargs):
        request.website.sale_reset()
        order = request.website.sale_get_order()
        if order and order.state in ['draft', 'cancel']:
            order.unlink()
        return request.redirect("/shop/product/%d" % product_id)

    @http.route('/booking/calendar/slots', type='json', auth='public', website=True)
    def get_free_slots(self, **kwargs):
        return request.env["sale.order.line"].sudo().get_free_slots(kwargs.get('start'),
                                                                    kwargs.get(
                                                                        'end'), kwargs.get('tz'),
                                                                    kwargs.get('domain', []))

    @http.route('/booking/calendar/slots/booked', type='json', auth='public', website=True)
    def get_booked_slots(self, **kwargs):
        return request.env["sale.order.line"].sudo().get_bookings(kwargs.get('start'),
                                                                  kwargs.get(
                                                                      'end'), kwargs.get('tz'),
                                                                  kwargs.get('domain', []))

    # @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    # def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
    #     res = request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=float(add_qty), set_qty=float(set_qty))
    #     line = request.registry["sale.order.line"].browse(request.cr, res.get('line_id'))[0]
    #     line.booking_start = kw.get('booking_start')
    #     print "Go for me!!! %s %s " % (kw.get('booking_start'), res.get('line_id'))
    #     return request.redirect("/shop/cart")

    @http.route('/booking/calendar/paid/<int:sale_order_id>', type='http', auth="user", website=True)
    def check_paid(self, sale_order_id, **post):
        order = request.env["sale.order"].sudo().sudo().browse(sale_order_id)
        need_qr = '1' if order.payment_tx_id.state == 'authorized' else '0'
        _logger.info('check payment state for %s: %s' % (order.name, need_qr))
        return need_qr

    @http.route('/booking/calendar/refund/<int:sale_order_id>', type='http', auth="user", website=True)
    def order_cancel(self, sale_order_id, **post):
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        result = _("Not Refundable")
        if order and order.check_refundable():
            if order.amount_total > 0:
                tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
                now = datetime.strftime(datetime.now(tz), '%Y-%m-%d %H:%M:%S')
                if order.payment_acquirer_id.provider == 'esun':
                    cust_url_method_name = '%s_get_form_action_cancel_url' % (
                        order.payment_acquirer_id.provider)
                    if hasattr(order.payment_acquirer_id, cust_url_method_name):
                        method = getattr(order.payment_acquirer_id,
                                         cust_url_method_name)
                        url = method()
                        _logger.info("url: %s" % url)
                        data = urllib.urlencode(order.form_cancel_generate_values())
                        _logger.info("data: %s" % data)
                        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "*/*", "User-Agent": "biznavi_ticket-app/1",}
                        req = urllib2.Request(url, data=data, headers=headers)
                        try:
                            res = urllib2.urlopen(req)
                        except urllib2.URLError as e:
                            if hasattr(e, 'reason'):
                                _logger.warn('We failed to reach a server.')
                                _logger.warn('Reason: %s' % e.reason)
                            elif hasattr(e, 'code'):
                                _logger.warn('The server couldn\'t fulfill the request.')
                                _logger.warn('Error code: %s' % e.code)
                        else:
                            res_str = res.read()
                            _logger.info(res_str)
                            try:
                                res_data = json.loads(res_str.split('=')[1])
                            except ValueError, e:
                                res_data = {'returnCode': 'API Error'}
                                _logger.error("%s Refund Error: %s" % (order.name, res_str))
                            payments = request.env['payment.transaction'].sudo().search([("sale_order_id", "=", sale_order_id)])
                            _logger.info("Order %s Refund Result: %s" % (order.name, res_data.get('returnCode')))
                            order.action_cancel()
                            if res_data.get('returnCode') == "00":
                                for payment in payments:
                                    payment.state = 'cancel'
                                    payment.state_message = u'退款時間 %s' % now
                                for line in order.order_line:
                                    line.remark1 = u'退款完成'
                                result = _("Ticket Refunded!")
                            else:
                                for payment in payments:
                                    payment.state = 'pending'
                                    payment.state_message = u'退款待處理 [%s] 退款時間 %s' % (res_data.get('returnCode'), now)
                                for line in order.order_line:
                                    line.remark1 = u'退款待處理'
                                result = _("Ticket Refund Processing!")
                else:
                    order.action_cancel()
                    payments = request.env['payment.transaction'].sudo().search([("sale_order_id", "=", sale_order_id)])
                    for payment in payments:
                        if payment.state == 'authorized':
                            payment.state = 'refund'
                            payment.refund_date = datetime.now()
                            payment.state_message = u'%s \n退款申請時間:%s' % (payment.state_message, now)
                            for line in order.order_line:
                                line.remark1 = u'退款'
                        elif payment.state == 'pending':
                            payment.state = 'cancel'
                            payment.state_message = u'%s \n退票申請時間:%s' % (payment.state_message, now)

                    result = _("Ticket Refund Processing!")
            else:
                order.action_cancel()
                result = _("Ticket Refunded!")
        return result

    @http.route('/booking/calendar/cancel_booking/<int:sale_order_id>', type='http', auth="user", website=True)
    def booking_cancel(self, sale_order_id, **post):
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        result = _("Not Cancelable")
        if order and order.check_refundable():
            order.action_cancel()
            result = _("Ticket Cancelled!")
        return result


class WebsiteSale(WebsiteSale):
    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        module = request.env['ir.module.module'].sudo().search([('name', '=', 'website_booking_calendar')])
        if module.state == 'installed':
            """ Method that should be called by the server when receiving an update
            for a transaction. State at this point :
    
             - UDPATE ME
            """
            if transaction_id is None:
                tx = request.website.sale_get_transaction()
                # return request.redirect('/')
            else:
                tx = request.env['payment.transaction'].sudo().browse(int(transaction_id))

            if sale_order_id is None:
                order = request.website.sale_get_order()
            else:
                order = request.env['sale.order'].sudo().browse(int(sale_order_id))
                # assert order.id == request.session.get('sale_last_order_id')
                request.session['sale_last_order_id'] = order.id

            if not order or (order.amount_total and not tx):
                return request.redirect('/my/orders')

            order.action_confirm()
            if (not order.amount_total and not tx) or tx.state in ['pending', 'done', 'authorized']:
                if (not order.amount_total and not tx):
                    # Orders are confirmed by payment transactions, but there is none for free orders,
                    # (e.g. free events), so confirm immediately
                    order.with_context(send_email=True).action_confirm()
            elif tx and tx.state == 'cancel':
                # cancel the quotation
                order.action_cancel()

            # clean context and session, then redirect to the confirmation page
            request.website.sale_reset()
            if tx and tx.state == 'draft':
                return request.redirect('/shop/payment')

            return request.redirect('/shop/confirmation')
        else:
            return super(WebsiteSale, self).payment_validate()

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        module = request.env['ir.module.module'].sudo().search([('name', '=', 'website_booking_calendar')])
        if module.state == 'installed':
            order = request.website.sale_get_order()

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

            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection

            order.onchange_partner_shipping_id()
            order.order_line._compute_tax_id()
            request.session['sale_last_order_id'] = order.id
            request.website.sale_get_order(update_pricelist=True)
            extra_step = request.env.ref('website_sale.extra_info_option')
            if extra_step.active:
                return request.redirect("/shop/extra_info")

            if order.pay_online:
                return request.redirect("/shop/payment")
            else:
                order.force_quotation_send()
                request.website.sale_reset()
                return request.redirect('/shop/confirmation')
        else:
            return super(WebsiteSale, self).confirm_order()


class WebsiteAccount(website_account):

    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sent'])
            # ('state', 'in', ['sent', 'cancel'])
        ]

        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = SaleOrder.search_count(domain)
        # make pager
        pager = request.website.pager(
            url="/my/quotes",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'quotations': quotations,
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/quotes',
        })
        return request.render("website_portal_sale.portal_my_quotations", values)

    @http.route(['/my/orders', '/my/orders/page/<int:page>', '/my/orders/search/<string:keyword>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, keyword=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        txs = request.env['payment.transaction'].sudo().search([('state', 'in', ['refund', 'done']), ('tx_no', '!=', '')])

        domain = ['&',
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            '|', ('state', 'in', ['sale']), ('id', 'in', [t.sale_order_id.id for t in txs])
        ]
        if keyword:
            domain.append(('name', 'ilike', keyword))
        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/orders',
        })
        return request.render("website_portal_sale.portal_my_orders", values)