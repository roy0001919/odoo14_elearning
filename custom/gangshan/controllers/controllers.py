# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import csv
import re
import datetime
from cStringIO import StringIO
import logging
from odoo.tools.misc import xlwt
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


class GangshanReport(http.Controller):
    search_fields = ['order_num', 'name', 'batch_info', 'order_user', 'buyer_tel',
                     'product_uom_qty', 'contact_usr', 'contact_tel', 'checkin_time']
    heaser_fields = [u'預訂編號', u'票種', u'日期梯次', u'預訂人', u'預訂人聯絡電話', u'人數', u'參訪人', u'參訪人聯絡電話', u'入場時間']
    # tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc

    @http.route('/gangshan/report', type='http', auth='public')
    @serialize_exception
    def download_bin(self, d, filename=None, **kw):
        sol = request.env['sale.order.line']
        # _logger.info('input d :%s' % d)
        res = sol.sudo().search_read(
            [('remark1', 'not in', [u'上線預扣']), ('state', 'in', ['sale', 'done']), ('p_date', '=', d),
             ('note', '=', False)], self.search_fields, order='booking_start')
        # _logger.info('res:%s' % res)

        return request.make_response(self.from_data_xls(res),
                                     headers=[('Content-Disposition', content_disposition(filename)),
                                              ('Content-Type', 'application/vnd.ms-excel')])

    @http.route('/gangshan/shuttle', type='http', auth='public')
    @serialize_exception
    def download_shuttle(self, d=datetime.datetime.now().strftime('%Y-%m-%d'), **kw):
        sol = request.env['sale.order.line']
        # _logger.info('input d :%s' % d)
        res = sol.sudo().search_read(
            [('remark1', 'not in', [u'上線預扣']), ('state', 'in', ['sale', 'done']), ('p_date', '=', d),
             ('team_id.id', '=', 2)], self.search_fields, order='booking_start')
        # _logger.info('res:%s' % res)

        return request.make_response(self.prodcatg_from_data_xls(res),
                                     headers=[('Content-Disposition', content_disposition('shuttle_%s.xls' % d)),
                                              ('Content-Type', 'application/vnd.ms-excel')])

    def from_data_xls(self, rows):
        tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        for i, fieldname in enumerate(self.heaser_fields):
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 8000  # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cv_key in enumerate(self.search_fields):
                # _logger.info('cv_key:%s' % cv_key)
                cell_value = row.get(cv_key)
                if cell_value and cv_key in ['order_user', 'contact_usr']:
                    cell_value = "".join(x if i != 1 else '*' for i, x in enumerate(cell_value))

                if cell_value and cv_key in ['checkin_time']:
                    cell_value = datetime.datetime.strftime(
                        datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                        '%Y/%m/%d %H:%M')

                # _logger.info('cell_value:%s' % cell_value)
                cell_style = base_style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                elif isinstance(cell_value, bool):
                    cell_value = ''

                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        worksheet.col(0).width = 256 * 16
        worksheet.col(1).width = 256 * 16
        worksheet.col(2).width = 256 * 30
        worksheet.col(3).width = 256 * 12
        worksheet.col(4).width = 256 * 16
        worksheet.col(5).width = 256 * 6
        worksheet.col(6).width = 256 * 12
        worksheet.col(7).width = 256 * 16
        worksheet.col(8).width = 256 * 26

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    def prodcatg_from_data_xls(self, rows):
        tz = pytz.timezone(request.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.tz) or pytz.utc
        workbook = xlwt.Workbook()
        s1 = workbook.add_sheet(u'套票')
        s2 = workbook.add_sheet(u'非套票')

        for i, fieldname in enumerate(self.heaser_fields):
            s1.write(0, i, fieldname)
            s1.col(i).width = 8000  # around 220 pixels
            s2.write(0, i, fieldname)
            s2.col(i).width = 8000  # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')
        s1Idx = 0
        s2Idx = 0
        for row_index, row in enumerate(rows):
            isSuit = True
            if row.get('name').find(u'套票') == -1:
                isSuit = False
                s2Idx += 1
            else:
                s1Idx += 1

            for cell_index, cv_key in enumerate(self.search_fields):
                # _logger.info('cv_key:%s' % cv_key)
                cell_value = row.get(cv_key)
                if cell_value and cv_key in ['order_user', 'contact_usr']:
                    cell_value = "".join(x if i != 1 else '*' for i, x in enumerate(cell_value))

                if cell_value and cv_key in ['checkin_time']:
                    cell_value = datetime.datetime.strftime(
                        datetime.datetime.strptime(cell_value, DTF).replace(tzinfo=pytz.utc).astimezone(tz),
                        '%Y/%m/%d %H:%M')

                # _logger.info('cell_value:%s' % cell_value)
                cell_style = base_style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                elif isinstance(cell_value, bool):
                    cell_value = ''

                if isSuit:
                    s1.write(s1Idx, cell_index, cell_value, cell_style)
                else:
                    s2.write(s2Idx, cell_index, cell_value, cell_style)

        s1.col(0).width = 256 * 16
        s1.col(1).width = 256 * 16
        s1.col(2).width = 256 * 30
        s1.col(3).width = 256 * 12
        s1.col(4).width = 256 * 16
        s1.col(5).width = 256 * 6
        s1.col(6).width = 256 * 12
        s1.col(7).width = 256 * 16
        s1.col(8).width = 256 * 26

        s2.col(0).width = 256 * 16
        s2.col(1).width = 256 * 16
        s2.col(2).width = 256 * 30
        s2.col(3).width = 256 * 12
        s2.col(4).width = 256 * 16
        s2.col(5).width = 256 * 6
        s2.col(6).width = 256 * 12
        s2.col(7).width = 256 * 16
        s2.col(8).width = 256 * 26

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    def from_data_csv(self, rows):
        fp = StringIO()
        writer = csv.writer(fp, quoting=csv.QUOTE_ALL)

        # writer.writerow([name.encode('utf-8') for name in self.heaser_fields])
        writer.writerow([h for h in self.heaser_fields])

        for data in rows:
            row = []
            # if isinstance(data, unicode):
            # 	try:
            # 		data = data.encode('utf-8')
            # 	except UnicodeError:
            # 		pass

            for fname in self.search_fields:
                row.append(data.get(fname))

            writer.writerow(row)

        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
