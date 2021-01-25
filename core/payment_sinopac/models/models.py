# coding: utf-8

from collections import OrderedDict
import logging
from hashlib import sha256
import json
import datetime, pytz
import requests

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AcquirerSinopac(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('sinopac', 'Sinopac')])
    sinopac_merchant_id = fields.Char('Merchant ID', required_if_provider='sinopac', groups='base.group_user')
    sinopac_terminal_id = fields.Char('Terminal ID', required_if_provider='sinopac', groups='base.group_user')
    sinopac_mac_key = fields.Char('Validate Key', required_if_provider='sinopac', groups='base.group_user')

    def get_sort_dict(self, values):
        keys = [
            'ONO', 'U', 'MID', 'BPF', 'IC', 'TA', 'TID',
        ]
        raw_values = OrderedDict()
        for k in keys:
            if k in values:
                raw_values[k] = values[k]

        data = '%s' % (json.dumps(raw_values).replace(' ', ''))
        return data

    def getAuthResURL(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        retURL = '%s/payment/sinopac/return' % base_url
        _logger.info('AuthResURL : %s' % retURL)
        return retURL

    def getResURL(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        retURL = '%s/payment/sinopac/inquery' % base_url
        _logger.info('AuthResURL : %s' % retURL)
        return retURL

    def _get_feature_support(self):
        res = super(AcquirerSinopac, self)._get_feature_support()
        res['authorize'].append('sinopac')
        return res

    @api.model
    def _get_sinopac_urls_new(self, environment):
        if environment == 'test':
            return {
                'sinopac_online_url': 'https://eposuat.sinopac.com/HPPRequest',
            }
        else:
            return {
                'sinopac_online_url': 'https://epos.sinopac.com/HPPRequest',
            }

    @api.model
    def _get_sinopac_urls(self, environment):
        if environment == 'test':
            return {
                'sinopac_online_url': 'https://www.focas-test.fisc.com.tw/FOCAS_WEBPOS/online/',
                'sinopac_debit_url': 'https://www.focas-test.fisc.com.tw/FOCAS_WEBPOS/debit/',
                'sinopac_upop_url': 'https://www.focas-test.fisc.com.tw/FOCAS_UPOP/upop/',
                'sinopac_tsmparm_url': 'https://www.focas-test.fisc.com.tw/FOCAS_WEBPOS/TSM_PARM/',
                'sinopac_tsmpage_url': 'https://www.focas-test.fisc.com.tw/FOCAS_WEBPOS/TSM_PAGE/'
            }
        else:
            return {
                'sinopac_online_url': 'https://www.focas.fisc.com.tw/FOCAS_WEBPOS/online/',
                'sinopac_debit_url': 'https://www.focas.fisc.com.tw/FOCAS_WEBPOS/debit/',
                'sinopac_upop_url': 'https://www.focas.fisc.com.tw/FOCAS_UPOP/upop/',
                'sinopac_tsmparm_url': 'https://www.focas.fisc.com.tw/FOCAS_WEBPOS/TSM_PARM/',
                'sinopac_tsmpage_url': 'https://www.focas.fisc.com.tw/FOCAS_WEBPOS/TSM_PAGE/'
            }

    @api.multi
    def _sinopac_generate_merchant_sig_sha256_new(self, values):
        print('data: %s' % values)
        return values

    @api.multi
    def sinopac_form_generate_values_new(self, values):
        _logger.info('sinopac_form_generate_values: %s' % values)
        post_val = {}
        post_val.update({
            'mid': self.sinopac_merchant_id,
            'tid': self.sinopac_terminal_id,
            'installment': '0',
            'oid': values['reference'],
            'transAmt': '%d' % int(tools.float_round(values['amount'], 2)),
            'transMode': '0',
            'AuthResURL': self.getAuthResURL(),
        })

        _logger.info('sinopac_form_generate_post_values: %s' % post_val)


        return post_val

    @api.multi
    def _sinopac_generate_merchant_sig_sha256(self, values):
        print('data: %s' % values)
        shasign = sha256(values).hexdigest()
        print('shasign: %s' % shasign)
        return shasign

    @api.multi
    def sinopac_form_generate_values(self, values):
        _logger.info('sinopac_form_generate_values: %s' % values)
        nowDatetime = datetime.datetime.now()
        localDate = nowDatetime.strftime('%Y%m%d')
        localTime = nowDatetime.strftime('%H%M%S')
        # 訂單編號 & 交易金額 & 驗證參數 & 特店代號 & 端末代號 & 交易時間
        # SHA-256(訂單編號lidm&交易金額authAmt&驗證參數&特店代號MerchantID&端末代號TerminalID&交易時間LocalDate+LocalTime)
        token_val = '%s&%s&%s&%s&%s&%s' % (values['reference'], values['amount'], self.sinopac_mac_key, self.sinopac_merchant_id, self.sinopac_terminal_id, nowDatetime.strftime('%Y%m%d%H%M%S'))

        token = self._sinopac_generate_merchant_sig_sha256(token_val)

        post_val = {}
        post_val.update({
            'MerchantID': self.sinopac_merchant_id,
            'TerminalID': self.sinopac_terminal_id,
            'merID': '28004668',
            'MerchantName': 'KHSkyWalkPark.com',
            'purchAmt': '%d' % int(tools.float_round(values['amount'], 2)),
            'lidm': values['reference'],
            'AutoCap': 1,  # 是否自動轉入請款檔作業 (0:no (default), 1:yes)
            # 'AuthResURL': '',  # 授權結果回傳網址
            'LocalDate': localDate,
            'LocalTime': localTime,
            'CurrencyNote': u'Siaogangshan Skywalk Park',
            'reqToken': token,
            'AuthResURL': self.getAuthResURL(),
        })
        return post_val

    @api.multi
    def sinopac_get_form_action_url(self):
        return self._get_sinopac_urls(self.environment)['sinopac_online_url']

    @api.model
    def update_sinopac_order_state(self):
        _logger.info("update_sinopac_order_state")
        inquery_url = 'https://www.focas.fisc.com.tw/FOCAS_WEBPOS/orderInquery/'
        nowDatetime = datetime.datetime.now() - datetime.timedelta(hours=2)
        localDate = nowDatetime.strftime('%Y-%m-%d %H:%M:%S')
        # _logger.info("localDate:%s" % localDate)
        txProvider = self.env['payment.acquirer'].search([('provider', '=', 'sinopac')])
        txs = self.env['payment.transaction'].search([('acquirer_id.provider', '=', 'sinopac'), ('state', '=', 'draft'), ('create_date', '>=', localDate)])
        # _logger.info("txProvider:%s" % txProvider)
        # _logger.info("txs:%s" % txs)
        data = {
            'MerchantID': txProvider.sinopac_merchant_id,
            'TerminalID': txProvider.sinopac_terminal_id,
            'merID': '28004668',
            'purchAmt': 0,
            'lidm': '',
            'ResURL': self.getResURL()
        }
        for tx in txs:
            data.update({
                'purchAmt': '%d' % int(tools.float_round(tx.amount, 2)),
                'lidm': tx.reference
            })
            _logger.info('data: %s' % data)
            r = requests.post(inquery_url, data=data)
            _logger.info('post: %s, %s \n %s' % (r.status_code, r.reason, r.text))
            retHtml = r.text
            if retHtml.find("name=txstatus value=0>") > 0 and retHtml.find("name=authCode") > 0 and retHtml.find("name=authCode value=>") < 0 and retHtml.find("name=xid") > 0 and retHtml.find("name=xid value=>") < 0:
                tx.state = 'authorized'
                tx.state_message = 'orderInquery: 狀態: 草稿->授權'
                tx.sale_order_id.state = 'sale'
                tx.sale_order_id.force_quotation_send()
            # else:
            #     print 'False'



    # 取消授權背端
    # @api.multi
    # def sinopac_get_form_action_cancel_url(self):
    #     return self._get_sinopac_urls(self.environment)['sinopac_online_url']
    #
    # @api.multi
    # def _sinopac_generate_merchant_sig_cancel_sha256(self, inout, values):
    #     def escapeVal(val):
    #         return val.replace('\\', '\\\\').replace(':', '\\:')
    #
    #     assert inout in ('in', 'out')
    #     assert self.provider == 'sinopac'
    #
    #     if inout == 'in':
    #         keys = [
    #             'ONO', 'MID',
    #         ]
    #     else:
    #         keys = [
    #             'RC', 'MID', 'ONO', 'LTD', 'LTT', 'RRN', 'AIR',
    #         ]
    #
    #     mac_key = self.sinopac_mac_key
    #     raw_values = OrderedDict()
    #     for k in keys:
    #         if k in values:
    #             raw_values[k] = values[k]
    #
    #     _logger.info('raw_values: %s' % raw_values)
    #     data = '%s%s' % (json.dumps(raw_values).replace(' ', ''), mac_key)
    #     _logger.info('raw_data: %s' % data)
    #     shasign = sha256(data).hexdigest()
    #     # print('shasign: %s' % shasign)
    #     return shasign
    #
    # @api.multi
    # def sinopac_form_cancel_generate_values(self, values):
    #     _logger.info('sinopac_form_cancel_generate_values: %s' % values)
    #     base_url = self.env['ir.config_parameter'].get_param('web.base.url')
    #     values.update({
    #         'ONO': values['reference'],
    #         'MID': self.esun_code,
    #     })
    #
    #     mac = self._sinopac_generate_merchant_sig_cancel_sha256('in', values)
    #
    #     post_val = {}
    #     post_val.update({
    #         'data': self.get_sort_dict(values),
    #         'mac': mac,
    #         'ksn': 1,
    #     })
    #     _logger.info("post_val: %s" % post_val);
    #     return post_val


class TxSinopac(models.Model):
    _inherit = 'payment.transaction'

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------
    @api.model
    def _sinopac_form_get_tx_from_data_new(self, data):
        _logger.info('_sinopac_form_get_tx_from_data: %s' % data)
        ret_status = data.get('responseCode')  # 回應碼
        ret_lidm = data.get('oid')  # Sale Order #
        ret_pan = data.get('pan')
        ret_transDate = data.get('transDate')
        ret_approveCode = data.get('approveCode')

        if ret_status not in ["00", "08", "11"]:
            error_msg = _('Sinopac: received data with missing reference (%s) or Response Code (%s)') % (ret_lidm, ret_status)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.env['payment.transaction'].search([('reference', '=', ret_lidm)])
        if ret_pan:
            tx.pay_no = ret_pan
            tx.pay_date = ret_transDate
            tx.trace_no = ret_approveCode

        if not tx or len(tx) > 1:
            error_msg = _('Sinopac: received data for reference %s') % (ret_lidm)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        _logger.info('_sinopac_form_get_tx_from_data (tx): %s' % tx)

        return tx

    def _sinopac_form_get_invalid_parameters_new(self, data):
        _logger.info('_sinopac_form_get_invalid_parameters: %s' % data)
        ret_status = data.get('responseCode')  # 授權結果狀態
        ret_lidm = data.get('oid')  # Sale Order #

        invalid_parameters = []
        # sale_order number
        if self.acquirer_reference and ret_lidm != self.acquirer_reference:
            invalid_parameters.append(('Reference', ret_lidm, self.acquirer_reference))
        # Response Code
        if ret_status not in ["00", "08", "11"]:
            invalid_parameters.append(('Result', ret_status, 'Transaction Fail.'))

        return invalid_parameters

    def _sinopac_form_validate_new(self, data):
        _logger.info('_sinopac_form_validate: %s' % data)
        ret_status = data.get('responseCode')  # 授權結果狀態
        ret_lidm = data.get('oid')  # Sale Order #
        ret_errDesc = data.get('responseMsg ')  # 授權失敗原因說明

        if ret_status in ["00", "08", "11"]:
            self.write({
                'state': 'authorized',
                'acquirer_reference': ret_lidm,
            })
            return True
        else:
            _logger.info(ret_errDesc)
            self.write({
                'state': 'error',
                'state_message': '%s: %s' % (ret_status, ret_errDesc)
            })
            return False

    @api.model
    def _sinopac_form_get_tx_from_data(self, data):
        _logger.info('_sinopac_form_get_tx_from_data: %s' % data)
        ret_status = data.get('status')  # 授權結果狀態
        # ret_authCode = data.get('authCode')  # 交易授權碼
        ret_lidm = data.get('lidm')  # Sale Order #

        if ret_status != "0":
            error_msg = _('Sinopac: received data with missing reference (%s) or Response Code (%s)') % (ret_lidm, ret_status)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        tx = self.env['payment.transaction'].search([('reference', '=', ret_lidm)])
        if not tx or len(tx) > 1:
            error_msg = _('Sinopac: received data for reference %s') % (ret_lidm)
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        _logger.info('_sinopac_form_get_tx_from_data (tx): %s' % tx)

        return tx

    def _sinopac_form_get_invalid_parameters(self, data):
        _logger.info('_sinopac_form_get_invalid_parameters: %s' % data)
        ret_status = data.get('status')  # 授權結果狀態
        ret_lidm = data.get('lidm')  # Sale Order #

        invalid_parameters = []
        # sale_order number
        if self.acquirer_reference and ret_lidm != self.acquirer_reference:
            invalid_parameters.append(('Reference', ret_lidm, self.acquirer_reference))
        # Response Code
        if ret_status not in ['0']:
            invalid_parameters.append(('Result', ret_status, 'Transaction Fail.'))

        return invalid_parameters

    def _sinopac_form_validate(self, data):
        _logger.info('_sinopac_form_validate: %s' % data)
        ret_status = data.get('status')  # 授權結果狀態
        ret_lidm = data.get('lidm')  # Sale Order #
        ret_errcode = data.get('errcode')  # 錯誤代碼
        ret_errDesc = data.get('errDesc')  # 授權失敗原因說明

        # tx = self.env['payment.transaction'].search([('reference', '=', data.get('lidm'))])

        if ret_status == '0':
            self.write({
                'state': 'authorized',
                'acquirer_reference': ret_lidm,
            })
            # if self.sale_order_id:
            #     self.sale_order_id.force_quotation_send()
            return True
        else:
            # error = _('Sinopac: feedback error')
            _logger.info(ret_errDesc)
            self.write({
                'state': 'error',
                'state_message': '%s: %s' % (ret_errcode, ret_errDesc)
            })
            return False

    # 取消授權背端
    # @api.model
    # def _sinopac_form_cancel_get_tx_from_data(self, data):
    #     _logger.info('_sinopac_form_cancel_get_tx_from_data: %s' % data)
    #     resp = data.get('DATA')
    #     resCode = resp.get('returnCode')
    #     txnData = resp.get('txnData')
    #
    #     reference = txnData.get('ONO')
    #     if resCode != "00":
    #         error_msg = _('Sinopac: received data with missing reference (%s) or Response Code (%s)') % (
    #         reference, resCode)
    #         _logger.info(error_msg)
    #         raise ValidationError(error_msg)
    #
    #     tx = self.env['payment.transaction'].search([('reference', '=', reference)])
    #     if not tx or len(tx) > 1:
    #         error_msg = _('Sinopac: received data for reference %s') % (reference)
    #         if not tx:
    #             error_msg += _('; no order found')
    #         else:
    #             error_msg += _('; multiple order found')
    #         _logger.info(error_msg)
    #         raise ValidationError(error_msg)
    #
    #     _logger.info('_sinopac_form_get_tx_from_data (tx): %s' % tx)
    #     # # verify shasign
    #     # shasign_check = tx.acquirer_id._esun_generate_merchant_sig('out', data)
    #     #
    #     # if shasign_check != data.get('M'):
    #     # 	error_msg = _('Esun: invalid merchantSig, received %s, computed %s') % (data.get('M'), shasign_check)
    #     # 	_logger.warning(error_msg)
    #     # 	raise ValidationError(error_msg)
    #
    #     return tx

    # 付款交易上方的"請款"按紐
    @api.multi
    def sinopac_s2s_capture_transaction(self, **kwargs):
        for tx in self:
            tx.state = 'done'
            tx.sale_order_id.status = 'done'

    # 付款交易上方的"取消授權"按紐
    @api.multi
    def sinopac_s2s_void_transaction(self, **kwargs):
        for tx in self:
            tx.state = 'cancel'
            tx.sale_order_id.status = 'cancel'

    @api.model
    def _capture_transaction_lastmonth(self, year_month=None):
        tz = pytz.timezone(self.env.context.get('tz') or 'UTC')
        if year_month:
            d = tz.localize(datetime.datetime.strptime(year_month, "%Y-%m")).astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
        else:
            d = tz.localize(datetime.datetime.utcnow().replace(day=1,hour=0,minute=0,second=0)).astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
        ptxs = self.env['payment.transaction'].search([('create_date', '<', d),('state', '=', 'authorized')])
        for ptx in ptxs:
            ptx.state = 'done'
