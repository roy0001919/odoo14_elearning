# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class AssemblyOrder(models.Model):
    _name = 'tokiku.assembly_order'

    name = fields.Char('Assembly Order Number', required=True, default='New', readonly=True)
    order_num = fields.Char('Assembly Order Number', compute='_compute_order_num')
    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project')
    file_date = fields.Date(string='File Date',
                            default=lambda self: datetime.now(pytz.timezone(self.env.user.partner_id.tz)).strftime(
                                '%Y-%m-%d'))
    run_date = fields.Date(string='Run Date', default=datetime.today())
    assembly_line_ids = fields.One2many('tokiku.assembly_order_line', 'assembly_order_id',
                                        string='Preparation Order Line')
    building = fields.Char('Building Number')
    partner_id = fields.Many2one('tokiku.supplier_info', string='Assembly Partner')
    factory_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory')

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
        self.assembly_line_ids = []

    @api.multi
    def item_select(self):
        self.ensure_one()
        project_id = self.env.context.get('default_project_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': project_id,
               'assembly_section': self.assembly_section,
               'panel_id': panel_id,
               'assembly_order_id': self.id
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'assembly_select_wizard_view')[1]

        return {
            'name': _('Assembly Order Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.assembly_select_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tokiku.assembly_order') or '/'

        return super(AssemblyOrder, self).create(vals)

    @api.multi
    def _compute_order_num(self):
        for o in self:
            o.order_num = '%s-%s-%s-%s' % (o.project_id.short_name, o.factory_id.supplier_id.ref, o.assembly_section, o.name[2:])

    @api.onchange('partner_id')
    def onchange_partner_id(self):

        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.project_id.id),
                                                        ('categ_id', '=', self.categ_id.id)])

        partner_ids = [l.supplier_id.id for l in panel.assembly_panel_line_ids]
        lines = []
        for l in panel.assembly_panel_line_ids:
            lines.append((0, 0, {
                'atlas_id': l.atlas_id.id,
                'building_id': l.building_id.id,
                'bom_id': l.bom_id.id,
                'demand_qty': l.total_demand,
            }))

            self.assembly_line_ids = lines

        return {'domain': {'partner_id': [('id', 'in', partner_ids)]}}


class AssemblyOrderLine(models.Model):
    _name = 'tokiku.assembly_order_line'

    # name = fields.Char (string='Part Number')
    assembly_panel_line_id = fields.Many2one('tokiku.assembly_panel_line')
    assembly_order_id = fields.Many2one('tokiku.assembly_order', string='Preparation Order', ondelete='cascade')

    atlas_id = fields.Many2one('tokiku.atlas', 'Atlas')
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')  # 組合編號
    # demand_qty = fields.Integer(string='Assembly Dispatch Qty')

    # Assembly
    estimated_qty = fields.Integer(string='Estimated Qty', compute='_compute_estimated_qty')
    assembly_qty = fields.Integer(string='Assembly Qty')
    done_qty = fields.Integer(string='Assembled Qty', compute='_compute_done_qty')
    due_qty = fields.Integer(string='Due Qty', compute='_compute_due_qty')
    run_date = fields.Date(string='Run Date', related='assembly_order_id.run_date', store=True)

    @api.multi
    def _compute_done_qty(self):
        for l in self:
            if l.assembly_order_id.assembly_section == u'框架':
                l.done_qty = l.assembly_panel_line_id.frame_assembled
            else:
                l.done_qty = l.assembly_panel_line_id.assembled

    @api.multi
    def _compute_estimated_qty(self):
        for l in self:
            if l.assembly_order_id.assembly_section == u'框架':
                l.estimated_qty = l.assembly_panel_line_id.frame_scheduled_assembly_qty
            else:
                l.estimated_qty = l.assembly_panel_line_id.scheduled_assembly_qty

    @api.multi
    @api.depends('assembly_order_id.state', 'assembly_order_id.run_date', 'assembly_order_id.assembly_line_ids',
                 'assembly_qty', 'done_qty')
    def _compute_due_qty(self):
        for l in self:
            past_orders = self.env['tokiku.assembly_order'].sudo().search(
                [('project_id', '=', l.env.user.project_id.id), ('state', '=', 'done'),
                 ('run_date', '<', l.assembly_order_id.run_date)])
            p_qty = 0
            d_qty = 0
            for o in past_orders:
                for ol in o.assembly_line_ids.filtered(
                        lambda x: x.bom_id.id == l.bom_id.id and x.building_id.id == l.building_id.id):
                    p_qty += ol.assembly_qty
                    d_qty += ol.done_qty
            l.due_qty = p_qty - d_qty
