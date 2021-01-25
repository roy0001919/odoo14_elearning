# -*- coding: utf-8 -*-
import logging
import pprint
from StringIO import StringIO

from datetime import datetime, timedelta
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

import werkzeug

from odoo import http, SUPERUSER_ID
from odoo.http import request
from requests.packages.urllib3.poolmanager import PoolManager
import requests
from requests.adapters import HTTPAdapter
import xml.etree.cElementTree as ET
import ssl
from hashlib import sha256

_logger = logging.getLogger(__name__)


class EasystoreController(http.Controller):
    _accept_url = '/payment/easystore/feedback'

    def _gen_sha256(self, values):
        shasign = sha256(values.encode()).hexdigest()
        return shasign

    @http.route([
        '/payment/easystore/return',
    ], type='http', auth='none', csrf=False)
    def transfer_return(self, **post):
        _logger.info('Beginning easystore_transfer_return with post data %s', pprint.pformat(post))  # debug

    @http.route([
        '/payment/easystore/receive',
    ], type='http', auth='none', csrf=False)
    def transfer_receive(self, **post):
        _logger.info('Receiving easystore payment data %s', pprint.pformat(post))  # debug

    @http.route([
        '/payment/easystore/feedback',
    ], type='http', auth='none', csrf=False)
    def transfer_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        baseUrl = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        defExpDay = (datetime.now() + timedelta(days=3)).replace(tzinfo=pytz.utc).astimezone(tz)

        pt = request.env['payment.transaction'].sudo().search([('reference', '=', post['reference'])])
        pt_order = pt.sale_order_id

        chk_booking_start = ''
        deadline = ''
        if pt_order and len(pt_order.order_line) > 0:
            chk_booking_start = '%s' % pt_order.order_line[0].booking_start
        else:
            return request.render('payment_easystore.payment_response_fail_redirect', {'return_url': '%s' % (baseUrl + '/shop/cart')})

        booking_start = (datetime.strptime(chk_booking_start, DTF) - timedelta(days=1)).replace(tzinfo=pytz.utc).astimezone(tz)
        if defExpDay < booking_start:
            chk_booking_start = defExpDay.strftime('%Y%m%d')
            deadline = defExpDay.strftime('%Y/%m/%d')
        else:
            chk_booking_start = booking_start.strftime('%Y%m%d')
            deadline = booking_start.strftime('%Y/%m/%d')

        s = requests.Session()
        s.mount('https://', EasystoreAdapter())
        resp = s.post(post['targetUrl'])
        wwwAuthDict = {}
        # _logger.info('resp : %s' % resp)
        if resp.status_code == 401:
            _logger.info('resp header: %s' % resp.headers)
            wwwAuth = resp.headers['WWW-Authenticate']
            if wwwAuth:
                authArr = wwwAuth.split(',')
                # _logger.info('authArr : %s' % authArr)
                for auth in authArr:
                    keyauth = auth.split('=')
                    wwwAuthDict.update({
                        keyauth[0].strip(): keyauth[1].replace('"', ""),
                    })

        wwwAuthRealm = wwwAuthDict['Digest realm']
        wwwAuthNonce = wwwAuthDict['nonce']
        wwwAuthQop = wwwAuthDict['qop']

        _logger.info('parameters : key_index:%s, key:%s, expDay:%s, rand_num:%s' % (post['sendKeyIdx'], post['sendKey'], chk_booking_start, post['ranNum']))

        ha1 = self._gen_sha256('%s:%s:%s' % (post['shopNum'], wwwAuthRealm, post['sendKey']))
        ha2 = self._gen_sha256('%s:%s' % ('POST', post['targetUrl']))
        # _logger.info('ha1 : %s' % ha1)
        # _logger.info('ha2 : %s' % ha2)

        xmlRoot = '<ATMOrIBonClientRequest xmlns="http://schemas.datacontract.org/2004/07/SinoPacWebAPI.Contract">'
        xmlContextSrc = """
                    <ShopNO>%s</ShopNO>
                    <KeyNum>%s</KeyNum>
                    <OrderNO>%s</OrderNO>
                    <Amount>%s</Amount>
                    <CurrencyID>NTD</CurrencyID>
                    <ExpireDate>%s</ExpireDate>
                    <PayType>A</PayType>
                    <PrdtName>%s</PrdtName>
                    <Memo></Memo>
                    <PayerName></PayerName>
                    <PayerMobile></PayerMobile>
                    <PayerAddress></PayerAddress>
                    <PayerEmail></PayerEmail>
                    <ReceiverName></ReceiverName>
                    <ReceiverMobile></ReceiverMobile>
                    <ReceiverAddress></ReceiverAddress>
                    <ReceiverEmail></ReceiverEmail>
                    <Param1></Param1>
                    <Param2></Param2>
                    <Param3></Param3>
                </ATMOrIBonClientRequest>
                """ % (post['shopNum'], post['sendKeyIdx'], post['reference'], int(float(post['amount']) * 100), chk_booking_start, post['clientName'])
        # post['partner_name'], post['partner_phone'], post['partner_address'], post['partner_email']
        xmlContext = xmlRoot.replace(' ', '') + xmlContextSrc.replace(' ', '').replace('\n', '').replace('\r', '')
        xmlContextSrc = xmlRoot + xmlContextSrc
        # _logger.info('xmlContext : %s' % xmlContext)

        verifyCode = self._gen_sha256('%s:%s:%s:%s:%s:%s' % (ha1, wwwAuthNonce, post['ranNum'], wwwAuthQop, xmlContext, ha2))

        # _logger.info('verifyCode : %s' % verifyCode)
        authStr = 'Digest realm="%s", nonce="%s", uri="%s", verifycode="%s", qop=%s, cnonce="%s"' % (wwwAuthRealm, wwwAuthNonce, post['targetUrl'], verifyCode, wwwAuthQop, post['ranNum'])
        # _logger.info('authStr = %s' % authStr)

        authHeader = {
            'Authorization': authStr,
            'content-type': 'text/xml;charset="utf-8"',
            'Accept': 'text/xml',
            'content-length': '%d' % len(xmlContextSrc)
        }

        req = requests.Request('POST', post['targetUrl'], data=xmlContextSrc, headers=authHeader)
        prepped = req.prepare()
        authResp = s.send(prepped, stream=True, timeout=120000)
        _logger.info('authResp status_code: %s' % authResp.status_code)

        # retry = 0
        # while authResp.status_code != 200 and retry < 3:
        #     try:
        #         retry += 1
        #         _logger.info('retry #%s authResp status_code: %s authStr: %s' % (retry, authResp.status_code, authStr))
        #         authResp = s.send(prepped, stream=True, timeout=120000)
        #     except ET.ParseError as err:
        #         _logger.info(err)

        if authResp.status_code != 200:
            return request.render('payment_easystore.payment_response_fail_redirect', {'return_url': '%s' % (baseUrl + '/shop/cart')})

        _logger.info('authResp body: %s' % authResp.text)
        root = ET.fromstring(authResp.text)

        txNo = ''
        payNo = ''
        ret_status = ''
        ret_desc = ''
        for child in root:
            if child.tag.find('TSNO') > 0:
                txNo = child.text

            if child.tag.find('PayNO') > 0:
                payNo = child.text

            if child.tag.find('Status') > 0:
                ret_status = child.text

            if child.tag.find('Description') > 0:
                ret_desc = child.text

        if ret_status == 'S':
            post.update({
                'txNo': txNo,
                'payNo': payNo,
                'deadline': deadline,
            })

            request.env['payment.transaction'].sudo().form_feedback(post, 'easystore')
            return werkzeug.utils.redirect(post.pop('return_url', '/'))
        else:
            _logger.info('Status = F, Error Code : %s' % ret_desc)
            return request.render('payment_easystore.payment_response_fail_redirect', {'return_url': '%s' % (baseUrl + '/shop/cart')})


class EasystoreAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2)