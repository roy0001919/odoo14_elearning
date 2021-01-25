# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz

from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)


class Preparation(models.Model):
    _name = 'tokiku.preparation_order'

    name = fields.Char('Preparation Order Num', required=True, default='New', readonly=True)
    order_num = fields.Char('Preparation Order Number', compute='_compute_order_num')
    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project')
    file_date = fields.Date(string='File Date',
                            default=lambda self: datetime.now(pytz.timezone(self.env.user.partner_id.tz)).strftime(
                                '%Y-%m-%d'))
    run_date = fields.Date(string='Run Date', default=datetime.today())
    preparation_line_ids = fields.One2many('tokiku.preparation_order_line', 'preparation_id',
                                           string='Preparation Order Line')
    # partner_id = fields.Many2one('res.partner', string='Assembly Factory')
    # building = fields.Char('Building Number')
    # preparation_form_num = fields.Char('Preparation Form Number', required=True, readonly=True, index=True, copy=False, default='New')
    partner_id = fields.Many2one('tokiku.supplier_info', string='Assembly Partner')  # 組裝廠
    partner_ref = fields.Char(related='partner_id.supplier_id.ref', string='Assembly Partner')
    factory_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory')
    factory_ref = fields.Char(related='factory_id.supplier_id.ref', string='Assembly Factory')

    assembly_section = fields.Selection([(u'框架', u'框架'), (u'框面', u'框面')], string='Assembly Section', required=True,
                                        default='框面')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def act_validate(self):
        self.write({'state': 'done'})

    @api.multi
    def act_cancel(self):
        self.write({'state': 'cancel'})

    @api.onchange('assembly_section')
    def onchange_assembly_section(self):
        self.preparation_line_ids = []

    @api.multi
    def item_select(self):
        self.ensure_one()
        project_id = self.env.context.get('default_project_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': project_id,
               'assembly_section': self.assembly_section,
               'panel_id': panel_id,
               'preparation_id': self.id
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'preparation_select_wizard_view')[1]

        return {
            'name': _('Preparation Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.preparation_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def act_preparation_order_print(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'tokiku.report_preparation_order',
        }

    @api.multi
    def act_production_order_print(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'tokiku.report_production_record',
        }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tokiku.preparation_order') or '/'

        return super(Preparation, self).create(vals)

    @api.multi
    def _compute_order_num(self):
        for o in self:
            o.order_num = '%s-%s-%s-%s' % (o.project_id.short_name, o.factory_id.supplier_id.ref, o.assembly_section, o.name[2:])


class PreparationLine(models.Model):
    _name = 'tokiku.preparation_order_line'

    # name = fields.Char(string='Part Number')
    assembly_panel_line_id = fields.Many2one('tokiku.assembly_panel_line')
    atlas_id = fields.Many2one('tokiku.atlas', 'Atlas')
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')  # 組合編號
    preparation_id = fields.Many2one('tokiku.preparation_order', string='Preparation Order', ondelete='cascade')
    # partner_id = fields.Many2one('res.partner', string='Assembly Factory')

    demand_qty = fields.Integer(string='Demand Qty')

    # Preparation
    estimated_qty = fields.Integer(string='Estimated Qty', compute='_compute_estimated_qty')  # 預定可組數
    prepared_qty = fields.Integer(string='Prepared Qty')  # 備料派工數
    rest_qty = fields.Integer(string='Rest Qty', compute='_compute_due_qty')  # 未備料數
    done_qty = fields.Integer(string='Done Qty', compute='_compute_done_qty')  # 備料已完成
    due_qty = fields.Integer(string='Due Qty', compute='_compute_due_qty')  # 已派工未完成數
    run_date = fields.Date(string='Run Date', related='preparation_id.run_date', store=True)

    @api.multi
    def _compute_done_qty(self):
        for l in self:
            if l.preparation_id.assembly_section == u'框架':
                l.done_qty = l.assembly_panel_line_id.frame_completed_prep
            else:
                l.done_qty = l.assembly_panel_line_id.completed_prep

    @api.multi
    def _compute_estimated_qty(self):
        for l in self:
            if l.preparation_id.assembly_section == u'框架':
                l.estimated_qty = l.assembly_panel_line_id.frame_scheduled_assembly_qty
            else:
                l.estimated_qty = l.assembly_panel_line_id.scheduled_assembly_qty

    @api.multi
    @api.depends('preparation_id.state', 'preparation_id.run_date', 'preparation_id.preparation_line_ids', 'demand_qty',
                 'prepared_qty', 'done_qty')
    def _compute_due_qty(self):
        for l in self:
            past_orders = self.env['tokiku.preparation_order'].sudo().search(
                [('project_id', '=', l.env.user.project_id.id), ('state', '=', 'done'),
                 ('run_date', '<', l.preparation_id.run_date)])
            p_qty = 0
            d_qty = 0
            for o in past_orders:
                for ol in o.preparation_line_ids.filtered(
                        lambda x: x.bom_id.id == l.bom_id.id and x.building_id.id == l.building_id.id):
                    p_qty += ol.prepared_qty
                    d_qty += ol.done_qty
            l.due_qty = p_qty - d_qty
            l.rest_qty = l.demand_qty - l.prepared_qty - d_qty

    #@api.constrains('prepared_qty','estimated_qty')#儲存後檢查
    #def check_prepared(self):
    #    for e in self:
    #       if e.prepared_qty > e.estimated_qty:
    #            raise ValidationError('Error')

    @api.onchange('prepared_qty','estimated_qty')
    def check_prepared_qty(self):
        for c in self:
            if c.prepared_qty > c.estimated_qty:
                c.prepared_qty = 0
                return {
                    'warning' : {
                        'message' : '不能大於預定可組數',
                    }
                }
            elif c.prepared_qty < 0:
                c.prepared_qty = 0
                return {
                    'warning' : {
                        'message' : '不能為負數',
                    }
                }
