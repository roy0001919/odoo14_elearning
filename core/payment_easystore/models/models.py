# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
from hashlib import sha256
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import requests
from random import randint
from datetime import datetime, timedelta
from lxml import etree

import logging
import pprint
import ssl

_logger = logging.getLogger(__name__)


class EasystorePaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('easystore', 'Easystore')])

    easystore_shop_num = fields.Char(string='Shop Num', required_if_provider='easystore', groups='base.group_user')
    easystore_client_name = fields.Char(string='Client Name', required_if_provider='easystore', groups='base.group_user')

    easystore_test_key_one = fields.Char(string='Test Key Data 1', required_if_provider='easystore', groups='base.group_user')
    easystore_test_key_two = fields.Char(string='Test Key Data 2', required_if_provider='easystore', groups='base.group_user')
    easystore_test_key_thr = fields.Char(string='Test Key Data 3', required_if_provider='easystore', groups='base.group_user')

    easystore_prod_key_one = fields.Char(string='Prod Key Data 1', required_if_provider='easystore', groups='base.group_user')
    easystore_prod_key_two = fields.Char(string='Prod Key Data 2', required_if_provider='easystore', groups='base.group_user')
    easystore_prod_key_thr = fields.Char(string='Prod Key Data 3', required_if_provider='easystore', groups='base.group_user')

    @api.model
    def _get_easystore_urls(self, environment):
        if environment == 'test':
            return {
                'easystore_url': 'https://sandbox.sinopac.com/WebAPI/Service.svc/CreateATMorIBonTrans',
                'easystore_query_url': 'https://sandbox.sinopac.com/WebAPI/Service.svc/QueryTradeStatus'
            }
        else:
            return {
                'easystore_url': 'https://ecapi.sinopac.com/WebAPI/Service.svc/CreateATMorIBonTrans',
                'easystore_query_url': 'https://ecapi.sinopac.com/WebAPI/Service.svc/QueryTradeStatus'
            }

    def get_key(self, environment):
        testKeyArr = [self.easystore_test_key_one, self.easystore_test_key_two, self.easystore_test_key_thr]
        prodKeyArr = [self.easystore_prod_key_one, self.easystore_prod_key_two, self.easystore_prod_key_thr]
        randIdx = randint(0, 2)
        if environment == 'test':
            return randIdx+1, testKeyArr[randIdx]
        else:
            return randIdx+1, prodKeyArr[randIdx]

    def easystore_get_form_action_url(self):
        return '/payment/easystore/feedback'

    @api.multi
    def _gen_sha256(self, values):
        print('data: %s' % values)
        shasign = sha256(values.encode()).hexdigest()
        print('shasign: %s' % shasign)
        return shasign

    @api.multi
    def easystore_form_generate_values(self, values):
        _logger.info('easystore_form_generate_values: %s' % values)

        sendKeyIdx, sendKey = self.get_key(self.environment)
        expDay = datetime.now() + timedelta(days=3)
        ranNum = randint(123400, 9999999)

        values.update({
            'failUrl': 'http://localhost:8069',
            'targetUrl': self._get_easystore_urls(self.environment)['easystore_url'],
            'clientName': self.easystore_client_name,
            'shopNum': self.easystore_shop_num,
            'sendKeyIdx': sendKeyIdx,
            'sendKey': sendKey,
            'expDay': expDay.strftime('%Y%m%d'),
            'ranNum': ranNum,
        })

        return values

    @api.model
    def update_easystore_transfer_state(self):
        _logger.info('check_easystore_transfer_state call!!')
        es = self.env['payment.acquirer'].search([('provider', '=', 'easystore')])

        targetUrl = self._get_easystore_urls(es.environment)['easystore_query_url']
        s = requests.Session()
        s.mount('https://', EasystoreAdapter())
        resp = s.post(targetUrl)
        wwwAuthDict = {}
        # _logger.info('resp : %s' % resp)
        if resp.status_code == 401:
            # _logger.info('resp header: %s' % resp.headers)
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

        testKeyArr = [es.easystore_test_key_one, es.easystore_test_key_two, es.easystore_test_key_thr]
        prodKeyArr = [es.easystore_prod_key_one, es.easystore_prod_key_two, es.easystore_prod_key_thr]
        randIdx = randint(0, 2)
        if es.environment == 'test':
            sendKeyIdx = randIdx + 1
            sendKey = testKeyArr[randIdx]
        else:
            sendKeyIdx = randIdx + 1
            sendKey = prodKeyArr[randIdx]
        expNow = datetime.now()
        expDayS = expNow - timedelta(days=5)
        expDayE = expNow + timedelta(days=1)
        ranNum = randint(123400, 9999999)

        # _logger.info('parameters : key_index:%s, key:%s, expDay:%s, rand_num:%s' % (sendKeyIdx, sendKey, expDay, ranNum))
        # _logger.info('parameters : expDayS:%s, expDayE:%s' % (expDayS.strftime('%Y%m%d'), expDayE.strftime('%Y%m%d')))

        ha1 = self._gen_sha256('%s:%s:%s' % (es.easystore_shop_num, wwwAuthRealm, sendKey))
        ha2 = self._gen_sha256('%s:%s' % ('POST', targetUrl))

        xmlRoot = '<QueryTradeStatusRequest xmlns="http://schemas.datacontract.org/2004/07/SinoPacWebAPI.Contract.QueryTradeStatus">'
        xmlContextSrc = """
                                <ShopNO>%s</ShopNO>
                                <KeyNum>%s</KeyNum>
                                <OrderNO></OrderNO>
                                <PayType>A</PayType>
                                <OrderDateS>%s</OrderDateS>
                                <OrderTimeS>0000</OrderTimeS>
                                <OrderDateE>%s</OrderDateE>
                                <OrderTimeE>0000</OrderTimeE>
                                <PayFlag>A</PayFlag>
                                <PrdtNameFlag>N</PrdtNameFlag>
                                <MemoFlag>N</MemoFlag>
                                <PayerNameFlag>N</PayerNameFlag>
                                <PayerMobileFlag>N</PayerMobileFlag>
                                <PayerAddressFlag>N</PayerAddressFlag>
                                <PayerEmailFlag>N</PayerEmailFlag>
                                <ReceiverNameFlag>N</ReceiverNameFlag>
                                <ReceiverMobileFlag>N</ReceiverMobileFlag>
                                <ReceiverAddressFlag>N</ReceiverAddressFlag>
                                <ReceiverEmailFlag>N</ReceiverEmailFlag>
                                <ParamFlag1>N</ParamFlag1>
                                <ParamFlag2>N</ParamFlag2>
                                <ParamFlag3>N</ParamFlag3>
                                <StagingFlag>N</StagingFlag>
                                <DividendFlag>N</DividendFlag>
                                </QueryTradeStatusRequest>
                        """ % (es.easystore_shop_num, sendKeyIdx, expDayS.strftime('%Y%m%d'), expDayE.strftime('%Y%m%d'))
        # post['partner_name'], post['partner_phone'], post['partner_address'], post['partner_email']
        xmlContext = xmlRoot.replace(' ', '') + xmlContextSrc.replace(' ', '').replace('\n', '').replace('\r', '')
        xmlContextSrc = xmlRoot + xmlContextSrc
        # _logger.info('xmlContext : %s' % xmlContext)

        verifyCode = self._gen_sha256('%s:%s:%s:%s:%s:%s' % (ha1, wwwAuthNonce, ranNum, wwwAuthQop, xmlContext, ha2))

        # _logger.info('verifyCode : %s' % verifyCode)
        authStr = 'Digest realm="%s", nonce="%s", uri="%s", verifycode="%s", qop=%s, cnonce="%s"' % (wwwAuthRealm, wwwAuthNonce, targetUrl, verifyCode, wwwAuthQop, ranNum)
        # _logger.info('authStr = %s' % authStr)

        authHeader = {
            'Authorization': authStr,
            'content-type': 'text/xml;charset="utf-8"',
            'Accept': 'text/xml',
            'content-length': '%d' % len(xmlContextSrc)
        }

        req = requests.Request('POST', targetUrl, data=xmlContextSrc, headers=authHeader)
        prepped = req.prepare()
        authResp = s.send(prepped, stream=True, timeout=120000)
        _logger.info('authResp status_code: %s' % authResp.status_code)
        respStr = '<QueryTradeStatusResponse>%s' % authResp.text[authResp.text.find('>')+1:]
        # _logger.info('respStr : %s' % respStr)
        if authResp.status_code == 200:
            root = etree.fromstring(respStr)
            for elem in root.iterfind('.//ECWebAPI'):
                OrderNO = elem.findtext('OrderNO')
                PayStatus = elem.findtext('PayStatus')
                _logger.info('OrderNO : %s, OrderNO: %s' % (OrderNO, PayStatus))
                if PayStatus == '010':  # 未付
                    pass
                elif PayStatus in ['020', '030', '040']:  # 已付
                    PayDate = elem.findtext('PayDate')
                    ptx = self.env['payment.transaction'].search([('reference', '=', OrderNO), ('state', 'in', ['pending', 'cancel'])])
                    if ptx:
                        if ptx.state == 'pending' and not ptx.refund_date:
                            ptx.state_message = u'%s \n付款日期:%s' % (ptx.state_message, PayDate)
                            ptx.state = 'authorized'
                            ptx.pay_date = PayDate
                            ptx.sale_order_id.note = u'%s \n付款日期:%s' % (ptx.sale_order_id.note, PayDate)
                            ptx.sale_order_id.state = 'sale'
                            ptx.sale_order_id.force_quotation_send()
                        elif ptx.state == 'cancel':
                            _logger.info(u'退票又匯款.....')
                            ptx.state_message = u'%s \n付款日期:%s' % (ptx.state_message, PayDate)
                            ptx.state = 'authorized'
                            ptx.pay_date = PayDate
                            ptx.refund_date = None
                            ptx.sale_order_id.note = u'%s \n付款日期:%s' % (ptx.sale_order_id.note, PayDate)
                            ptx.sale_order_id.state = 'sale'
                            ptx.sale_order_id.force_quotation_send()
                            # ptx.state_message = u'%s \n付款日期:%s' % (ptx.state_message, PayDate)
                            # ptx.state = 'refund'
                            # ptx.pay_date = PayDate
                            # ptx.sale_order_id.note = u'%s \n付款日期:%s' % (ptx.sale_order_id.note, PayDate)
                elif PayStatus == '110':    # 逾期未付
                    ExpireDate = elem.findtext('ExpireDate')
                    ptx = self.env['payment.transaction'].search([('reference', '=', OrderNO), ('state', '=', 'pending')])
                    if ptx:
                        ptx.state_message = u'%s \n逾期未付:%s' % (ptx.state_message, ExpireDate)
                        ptx.state = 'cancel'
                        ptx.exp_date = ExpireDate
                        ptx.sale_order_id.note = u'%s \n逾期未付:%s' % (ptx.sale_order_id.note, ExpireDate)
                        ptx.sale_order_id.state = 'cancel'


class EasystorePaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _easystore_form_get_tx_from_data(self, data):

        _logger.info('_easystore_form_get_tx_from_data : %s' % data)

        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        txNo, payNo, deadline = data.get('txNo'), data.get('payNo'), data.get('deadline')
        tx = self.env['payment.transaction'].search([('reference', '=', reference)])

        if not payNo or payNo == 'None':
            raise ValidationError('Pay Number not found')

        if not txNo or txNo == 'None':
            raise ValidationError('Transaction Number not found')

        if not deadline or deadline == 'None':
            raise ValidationError('Deadline not found')

        if payNo:
            tx.pay_no = payNo
            tx.sale_order_id.note = u'匯款帳號: %s' % payNo
        if txNo:
            tx.tx_no = txNo
        if txNo and payNo:
            tx.state_message = u'匯款帳號: %s, 交易編號: %s' % (payNo, txNo)
        if deadline:
            tx.deadline = deadline

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _easystore_form_get_invalid_parameters(self, data):

        _logger.info('_easystore_form_get_invalid_parameters : %s' % data)

        invalid_parameters = []
        txNo, payNo, deadline = data.get('txNo'), data.get('payNo'), data.get('deadline')

        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        if not txNo or txNo == 'None':
            invalid_parameters.append(('txNo', txNo, 'Transaction Number not found'))

        if not payNo or payNo == 'None':
            invalid_parameters.append(('payNo', payNo, 'Pay Number not found'))

        if not deadline or deadline == 'None':
            invalid_parameters.append(('deadline', deadline, 'Deadline not found'))

        return invalid_parameters

    def _easystore_form_validate(self, data):
        _logger.info('_easystore_form_validate : %s' % data)
        _logger.info('Validated transfer payment for tx %s: set as pending' % (self.reference))
        return self.write({'state': 'pending'})

    # 付款交易上方的"請款"按紐
    @api.multi
    def easystore_s2s_capture_transaction(self, **kwargs):
        for tx in self:
            tx.state = 'done'
            tx.sale_order_id.status = 'done'

    # 付款交易上方的"取消授權"按紐
    @api.multi
    def easystore_s2s_void_transaction(self, **kwargs):
        for tx in self:
            tx.state = 'cancel'
            tx.sale_order_id.status = 'cancel'


class EasystoreAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1_2)