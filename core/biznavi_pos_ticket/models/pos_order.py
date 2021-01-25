# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
import pytz

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

pos_to_sync = {}


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details_by_config(self, config_id, date_start=False, date_stop=False):
        # _logger.info('config_id: %s' % config_id)
        configs = self.env['pos.config'].search([('id', '=', config_id)])

        return self.get_sale_details(False, False, configs)

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, configs=False):
        """ Serialise the orders of the day information

        params: date_start, date_stop string representing the datetime of order
        """
        if not configs:
            configs = self.env['pos.config'].search([])

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
        today = today.astimezone(pytz.timezone('UTC'))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            # start by default today 00:00:00
            date_start = today

        if date_stop:
            # set time to 23:59:59
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            # stop by default today 23:59:59
            date_stop = today + timedelta(days=1, seconds=-1)

        # avoid a date_stop smaller than date_start
        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        orders = self.env['pos.order'].search([
            ('date_order', '>=', date_start),
            ('date_order', '<=', date_stop),
            ('state', 'in', ['paid','invoiced','done']),
            ('config_id', 'in', configs.ids),
            ('pos_reference', 'like', '-')])

        user_currency = self.env.user.company_id.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id.compute(order.amount_total, user_currency)
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'total':0.0})
                        taxes[tax['id']]['total'] += tax['amount']

        st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)]).ids
        if st_line_ids:
            self.env.cr.execute("""
                SELECT aj.name, sum(amount) total
                FROM account_bank_statement_line AS absl,
                     account_bank_statement AS abs,
                     account_journal AS aj 
                WHERE absl.statement_id = abs.id
                    AND abs.journal_id = aj.id 
                    AND absl.id IN %s 
                GROUP BY aj.name
            """, (tuple(st_line_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []

        return {
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.user.company_id.name,
            'taxes': taxes.values(),
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'variant_name': product.display_name.replace(product.name, '').replace("(", '').replace(")", ''),
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'uom': product.uom_id.with_context(lang='zh_TW').name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def write(self, vals):
        for p in pos_to_sync:
            pos_to_sync[p] = True
        return super(SaleOrderLine, self).write(vals)

    @api.model
    def create(self, values):
        for p in pos_to_sync:
            pos_to_sync[p] = True
        return super(SaleOrderLine, self).create(values)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def write(self, vals):
        for p in pos_to_sync:
            pos_to_sync[p] = True
        return super(PosOrder, self).write(vals)

    @api.model
    def pos_sync(self, config_id):
        # if pos_to_sync.get(config_id):
        #     pos_to_sync[config_id] = False
        #     # print "need sync"
        #     return True
        # else:
        #     pos_to_sync.setdefault(config_id, False)
        #     # print "no need sync"
        #     return False
        return True
