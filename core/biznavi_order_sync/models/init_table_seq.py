# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class InitTableSeq(models.Model):
    _name = "biznavi_order_sync.init_table_seq"

    @api.model
    def updateSeq(self):
        cr = self.env.cr
        cr.execute("ALTER SEQUENCE sale_order_id_seq MINVALUE -2147483648 RESTART -2147483648")
        cr.execute("ALTER SEQUENCE sale_order_line_id_seq MINVALUE -2147483648 RESTART -2147483648")
        return True
