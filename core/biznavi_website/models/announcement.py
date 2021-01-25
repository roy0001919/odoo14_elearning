# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
import pytz
import logging

_logger = logging.getLogger(__name__)


class Announcement(models.Model):
    _name = 'biznavi_website.announcement'
    _description = 'Announcement'

    name = fields.Char(string="Subject")
    content = fields.Text(string="Content")
    date_from = fields.Datetime(string="Date start")
    date_to = fields.Datetime(string="Date end")
    color = fields.Char('Color', default="#007700")
    active = fields.Boolean(string="Active", default=True)

