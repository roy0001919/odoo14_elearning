# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import re
import datetime
from cStringIO import StringIO
import logging
from odoo.tools.misc import xlwt
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


class GangshanReport(http.Controller):
    search_fields = ['order_name', 'order_partner', 'order_note', 'order_amount_total', 'tx_state_message', 'order_line']
    search_line_fields = ['name', 'product_uom_qty', 'price_unit', 'price_sub_total', 'booking_start']
    header_fields = [u'訂單編號', u'預訂人', u'付款資訊', u'總價', u'交易資訊', u'票種', u'數量', u'單價', u'小計', u'梯次開始時間']
    header_all_fields = [u'梯次開始時間', u'一般民眾 (全票80元)', u'一般民眾 (半票40元)', u'一般民眾 (免費票)', u'套票 (全票)', u'套票 (半票)', u'一卡通 (全票80元)', u'一卡通 (半票40元)', u'團體旅客20 (全票80元)', u'團體旅客20 (半票40元)', u'團體旅客100 (全票80元)', u'團體旅客100 (半票40元)', u'訂單編號', u'付款資訊', u'交易資訊', u'試營運 (全票80元)', u'試營運 (半票40元)', u'試營運 (全票)', u'試營運 (半票)']

    def _get_date_range(self, d):

        dateArr = d.split(',')
        ds = dateArr[0]
        de = dateArr[1]

        retArr = [ds]
        tmpDe = datetime.datetime.strptime(de, '%Y-%m-%d')
        for i in range(1, 90):
            tmpDs = datetime.datetime.strptime(ds, '%Y-%m-%d') + datetime.timedelta(days=i)
            if tmpDs <= tmpDe:
                retArr.append(tmpDs.strftime('%Y-%m-%d'))
            else:
                break

        _logger.info('retArr :%s' % retArr)

        return retArr


    @http.route('/biznavi_payment_transaction/report', type='http', auth='public')
    @serialize_exception
    def download_bin(self, d, filename=None, **kw):
        dArr = self._get_date_range(d)
        sinoPayment = []
        easystorePayment = []
        dirSale = []
        # sols = request.env['sale.order.line'].sudo().search([('state', 'in', ['sale', 'done']), ('p_date', 'like', month_p_date)])
        sols = request.env['sale.order.line'].sudo().search([('state', 'in', ['sale', 'done']), ('p_date', 'in', dArr)])
        sos = request.env['sale.order'].sudo().search([('order_line.id', 'in', sols.ids)])
        for so in sos:
            tx = so.payment_tx_id
            if tx and tx.state == 'authorized':
                provider = tx.acquirer_id.provider
                if provider == 'easystore':
                    tmpOrderLines = []
                    tmpBookingStart = ''
                    for sol in so.order_line:
                        tmpLineDict = {
                            'name': sol.name,
                            'product_uom_qty': sol.product_uom_qty,
                            'price_unit': sol.price_unit,
                            'booking_start': sol.booking_start,
                            'price_sub_total': float(sol.product_uom_qty) * float(sol.price_unit),
                        }
                        tmpBookingStart = sol.booking_start
                        tmpOrderLines.append(tmpLineDict)

                    tmpEsaystoreDict = {
                        'order_name': so.name,
                        'order_partner': so.partner_id.name,
                        'order_note': so.note,
                        'order_amount_total': so.amount_total,
                        'tx_state_message': so.payment_tx_id.state_message,
                        'booking_start': tmpBookingStart,
                        'order_line': tmpOrderLines,
                    }
                    easystorePayment.append(tmpEsaystoreDict)

                if provider == 'sinopac':
                    tmpOrderLines = []
                    tmpBookingStart = ''
                    for sol in so.order_line:
                        tmpLineDict = {
                            'name': sol.name,
                            'product_uom_qty': sol.product_uom_qty,
                            'price_unit': sol.price_unit,
                            'booking_start': sol.booking_start,
                            'price_sub_total': float(sol.product_uom_qty) * float(sol.price_unit),
                        }
                        tmpBookingStart = sol.booking_start
                        tmpOrderLines.append(tmpLineDict)

                    tmpSinopacDict = {
                        'order_name': so.name,
                        'order_partner': so.partner_id.name,
                        'order_note': so.note,
                        'order_amount_total': so.amount_total,
                        'tx_state_message': so.payment_tx_id.state_message,
                        'booking_start': tmpBookingStart,
                        'order_line': tmpOrderLines,
                    }
                    sinoPayment.append(tmpSinopacDict)
            elif not tx:
                tmpOrderLines = []
                tmpBookingStart = ''
                for sol in so.order_line:
                    tmpLineDict = {
                        'name': sol.name,
                        'product_uom_qty': sol.product_uom_qty,
                        'price_unit': sol.price_unit,
                        'booking_start': sol.booking_start,
                        'price_sub_total': float(sol.product_uom_qty) * float(sol.price_unit),
                    }
                    tmpBookingStart = sol.booking_start
                    tmpOrderLines.append(tmpLineDict)

                tmpDirDict = {
                    'order_name': so.name,
                    'order_partner': so.partner_id.name,
                    'order_note': so.note,
                    'order_amount_total': so.amount_total,
                    'tx_state_message': '',
                    'booking_start': tmpBookingStart,
                    'order_line': tmpOrderLines,
                }
                dirSale.append(tmpDirDict)

        return request.make_response(self.from_data_xls(sinoPayment, easystorePayment, dirSale),
                                     headers=[('Content-Disposition', content_disposition(filename)),
                                              ('Content-Type', 'application/vnd.ms-excel')])

    def from_data_xls(self, sinoPayment, easystorePayment, dirSale):
        tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        workbook = xlwt.Workbook(style_compression=2)
        s1 = workbook.add_sheet(u'信用卡', cell_overwrite_ok=True)
        s2 = workbook.add_sheet(u'匯款', cell_overwrite_ok=True)

        for i, fieldname in enumerate(self.header_fields):
            s1.write(0, i, fieldname)
            s1.col(i).width = 8000  # around 220 pixels
            s2.write(0, i, fieldname)
            s2.col(i).width = 8000  # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        s1Idx = 0
        for row_index, row in enumerate(sinoPayment):
            s1Idx += 1
            for cell_index, cv_key in enumerate(self.search_fields):
                cell_value = row.get(cv_key)

                if cell_value and cv_key in ['booking_start']:
                    cell_value = datetime.datetime.strftime(
                        datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                        '%Y/%m/%d %H:%M')

                cell_style = base_style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                elif isinstance(cell_value, bool):
                    cell_value = ''

                if cv_key in ['order_line']:
                    if cell_value and cv_key in ['order_line']:
                        for l_row_idx, l_row in enumerate(cell_value):
                            s1Idx += 1
                            for l_cell_idx, l_cv_key in enumerate(self.search_line_fields):
                                l_cell_value = l_row.get(l_cv_key)

                                if cell_value and cv_key in ['booking_start']:
                                    cell_value = datetime.datetime.strftime(datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%Y/%m/%d %H:%M')

                                cell_style = base_style
                                if isinstance(cell_value, basestring):
                                    cell_value = re.sub("\r", " ", cell_value)
                                elif isinstance(cell_value, datetime.datetime):
                                    cell_style = datetime_style
                                elif isinstance(cell_value, datetime.date):
                                    cell_style = date_style
                                elif isinstance(cell_value, bool):
                                    cell_value = ''

                                s1.write(s1Idx, (cell_index + l_cell_idx), l_cell_value, cell_style)

                else:
                    s1.write(s1Idx, cell_index, cell_value, cell_style)

        s2Idx = 0
        for row_index, row in enumerate(easystorePayment):
            s2Idx += 1
            for cell_index, cv_key in enumerate(self.search_fields):
                cell_value = row.get(cv_key)

                if cell_value and cv_key in ['booking_start']:
                    cell_value = datetime.datetime.strftime(
                        datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                        '%Y/%m/%d %H:%M')

                cell_style = base_style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                elif isinstance(cell_value, bool):
                    cell_value = ''

                if cv_key in ['order_line']:
                    if cell_value and cv_key in ['order_line']:
                        for l_row_idx, l_row in enumerate(cell_value):
                            s2Idx += 1
                            for l_cell_idx, l_cv_key in enumerate(self.search_line_fields):
                                l_cell_value = l_row.get(l_cv_key)

                                if cell_value and cv_key in ['booking_start']:
                                    cell_value = datetime.datetime.strftime(datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%Y/%m/%d %H:%M')

                                cell_style = base_style
                                if isinstance(cell_value, basestring):
                                    cell_value = re.sub("\r", " ", cell_value)
                                elif isinstance(cell_value, datetime.datetime):
                                    cell_style = datetime_style
                                elif isinstance(cell_value, datetime.date):
                                    cell_style = date_style
                                elif isinstance(cell_value, bool):
                                    cell_value = ''

                                s2.write(s2Idx, (cell_index + l_cell_idx), l_cell_value, cell_style)

                else:
                    s2.write(s2Idx, cell_index, cell_value, cell_style)

        s1.col(0).width = 256 * 15
        s1.col(1).width = 256 * 15
        s1.col(2).width = 256 * 30
        s1.col(3).width = 256 * 8
        s1.col(4).width = 256 * 30
        s1.col(5).width = 256 * 20
        s1.col(6).width = 256 * 8
        s1.col(7).width = 256 * 8
        s1.col(8).width = 256 * 8
        s1.col(9).width = 256 * 20

        s2.col(0).width = 256 * 15
        s2.col(1).width = 256 * 15
        s2.col(2).width = 256 * 30
        s2.col(3).width = 256 * 8
        s2.col(4).width = 256 * 30
        s2.col(5).width = 256 * 20
        s2.col(6).width = 256 * 8
        s2.col(7).width = 256 * 8
        s2.col(8).width = 256 * 8
        s2.col(9).width = 256 * 20

        s3 = workbook.add_sheet(u'清分', cell_overwrite_ok=True)
        for i, fieldname in enumerate(self.header_all_fields):
            s3.write(0, i, fieldname)
            s3.col(i).width = 8000  # around 220 pixels

        allPay = sinoPayment + easystorePayment + dirSale
        allPayments = sorted(allPay, key=lambda k: k['booking_start'])
        for row_index, row in enumerate(allPayments):
            # so number, note and transaction note
            cell_value, cell_style = self._get_cell(row.get('booking_start'), tz, True)
            s3.write(row_index + 2, 0, cell_value, cell_style)
            cell_value, cell_style = self._get_cell(row.get('order_name'), tz)
            s3.write(row_index + 2, 12, cell_value, cell_style)
            cell_value, cell_style = self._get_cell(row.get('order_note'), tz)
            s3.write(row_index + 2, 13, cell_value, cell_style)
            cell_value, cell_style = self._get_cell(row.get('tx_state_message'), tz)
            s3.write(row_index + 2, 14, cell_value, cell_style)

            for line in row.get('order_line'):
                prodName = line.get('name')
                prodQty, cell_style = self._get_cell(line.get('product_uom_qty'), tz)
                prodIdx = self.header_all_fields.index(prodName)
                if prodIdx >= 1:
                    # tmpCell = s3.cell(row=row_index + 1, column=prodIdx)
                    # if tmpCell.value:
                    #     prodQty += tmpCell.value

                    s3.write(row_index + 2, prodIdx, prodQty, cell_style)

        s3.write(1, 1, xlwt.Formula('SUM(B3:B%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 2, xlwt.Formula('SUM(C3:C%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 3, xlwt.Formula('SUM(D3:D%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 4, xlwt.Formula('SUM(E3:E%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 5, xlwt.Formula('SUM(F3:F%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 6, xlwt.Formula('SUM(G3:G%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 7, xlwt.Formula('SUM(H3:H%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 8, xlwt.Formula('SUM(I3:I%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 9, xlwt.Formula('SUM(J3:J%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 10, xlwt.Formula('SUM(K3:K%s)' % (len(allPayments)+2)), base_style)
        s3.write(1, 11, xlwt.Formula('SUM(L3:L%s)' % (len(allPayments)+2)), base_style)

        s3.col(0).width = 256 * 15
        s3.col(1).width = 256 * 20
        s3.col(2).width = 256 * 20
        s3.col(3).width = 256 * 20
        s3.col(4).width = 256 * 20
        s3.col(5).width = 256 * 20
        s3.col(6).width = 256 * 20
        s3.col(7).width = 256 * 20
        s3.col(8).width = 256 * 20
        s3.col(9).width = 256 * 20
        s3.col(10).width = 256 * 20
        s3.col(11).width = 256 * 30
        s3.col(12).width = 256 * 30

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    def _get_cell(self, val, tz, needFormat=False):
        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        cell_value = val

        if needFormat :
            cell_value = datetime.datetime.strftime(
                datetime.datetime.strptime(val, DTF).replace(tzinfo=pytz.utc).astimezone(tz), '%Y/%m/%d %H:%M')

        cell_style = base_style
        if isinstance(val, basestring):
            cell_value = re.sub("\r", " ", val)
        elif isinstance(val, datetime.datetime):
            cell_style = datetime_style
        elif isinstance(val, datetime.date):
            cell_style = date_style
        elif isinstance(val, bool):
            cell_value = ''

        return cell_value, cell_style