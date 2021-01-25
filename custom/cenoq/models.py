# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_formula = fields.Char(string="Price Formula")

    @api.onchange('price_formula')
    def _onchange_price_formula(self):
        if self.price_formula:
            self.price_unit = eval(self.price_formula)
