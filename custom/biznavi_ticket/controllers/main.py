# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import Forbidden

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleBooking(WebsiteSale):
    def get_attribute_value_ids(self, product):
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 0).mapped('attribute_id').ids
        to_currency = request.website.get_current_pricelist().currency_id
        attribute_value_ids = []
        for variant in product.product_variant_ids:
            if to_currency != product.currency_id:
                price = variant.currency_id.compute(variant.website_public_price, to_currency) / quantity
            else:
                price = variant.website_public_price / quantity
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids if v.attribute_id.id in visible_attrs_ids]
            attribute_value_ids.append([variant.id, visible_attribute_ids, variant.website_price, price])
        return attribute_value_ids

    def _get_mandatory_billing_fields(self):
        return ["name", "email", "city", "street", "country_id"]

    def _get_mandatory_shipping_fields(self):
        return ["name", "street", "country_id"]

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True)
    def address(self, **kw):
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order(force_create=1)
        mode = (False, False)
        def_country_id = order.partner_id.country_id
        values, errors = {}, {}

        partner_id = int(kw.get('partner_id', -1))

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                        mode = ('edit', 'billing')
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect('/shop/checkout')

        # IF POSTED
        if 'submitted' in kw:
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)

                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.onchange_partner_id()
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get('callback') or '/shop/checkout')

        country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
        country = country and country.exists() or def_country_id
        render_values = {
            'partner_id': partner_id,
            'mode': mode,
            'checkout': values,
            'country': country,
            'countries': country.get_website_sale_countries(mode=mode[1]),
            "states": country.get_website_sale_states(mode=mode[1]),
            'error': errors,
            'callback': kw.get('callback'),
        }
        return request.render("website_sale.address", render_values)

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            return request.redirect('/shop/address')

        for f in self._get_mandatory_billing_fields():
            if not order.partner_id[f]:
                return request.redirect('/shop/address?partner_id=%d' % order.partner_id.id)

        values = self.checkout_values(**post)

        # Avoid useless rendering if called in ajax
        if post.get('xhr'):
            return 'ok'
        if order.check_bookable():
            return request.render("website_sale.checkout", values)
        else:
            return request.redirect('/shop/product/%d?RC=timeover' % order.order_line[0].product_id.product_tmpl_id.id)

    @http.route('/booking/calendar/contact_modify/<int:line_id>', type='http', auth="user", website=True)
    def order_line_modify(self, line_id, **post):
        line = request.env['sale.order.line'].sudo().browse(line_id)
        result = '{"msg": "%s"}' % _("Modify failed!")
        if line:
            if post.get('contact_usr').strip() == "" or post.get('contact_tel').strip() == "":
                result = '{"contact_usr": "%s", "contact_tel": "%s"}' % (line.contact_usr, line.contact_tel)
            else:
                line.contact_usr =  post.get('contact_usr') 
                line.contact_tel =  post.get('contact_tel') 
                result = '{"contact_usr": "%s"}' % line.contact_usr
        return result

    @http.route('/booking/calendar/refund_info/<int:tx_id>', type='http', auth="user", website=True)
    def refund_info_modify(self, tx_id, **post):
        tx = request.env['payment.transaction'].sudo().browse(tx_id)
        result = '{"msg": "%s"}' % _("Modify failed!")
        if tx:
            tx.refund_bank = post.get('refund_bank')
            tx.refund_bank_code = post.get('refund_bank_code')
            tx.refund_branch_code = post.get('refund_branch_code')
            tx.refund_name = post.get('refund_name')
            tx.refund_account = post.get('refund_account')
            result = '{"refund_bank": "%s", "refund_bank_code": "%s", "refund_branch_code": "%s", "refund_name": "%s", "refund_account": "%s"}' % (tx.refund_bank, tx.refund_bank_code, tx.refund_branch_code, tx.refund_name, tx.refund_account)
        return result
