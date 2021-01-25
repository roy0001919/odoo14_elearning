# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ProductionRecord(models.Model):
    _name = 'tokiku.production_record'

    name = fields.Char('Name', required=True, default='New', readonly=True)
    order_num = fields.Char('Production Record Order Number', compute='_compute_order_num')
    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project')
    file_date = fields.Date(string='File Date',
                            default=lambda self: datetime.now(pytz.timezone(self.env.user.partner_id.tz)).strftime(
                                '%Y-%m-%d'))
    run_date = fields.Date(string='Run Date', default=datetime.today())
    production_record_line_ids = fields.One2many('tokiku.production_record_line', 'production_record_id',
                                                 string='Production Record Line')
    building = fields.Char('Building Number')
    assembly_section = fields.Selection([(u'框架', u'框架'), (u'框面', u'框面')], string='Assembly Section', required=True,
                                        default='框面')
    supplier_info_id = fields.Many2one('tokiku.supplier_info', string='Assembly Partner', change_default=False)
    partner_id = fields.Many2one('res.partner', related='supplier_info_id.supplier_id')
    factory_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory')  # 供應商

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def act_validate(self):
        self.write({'state': 'done'})
        location_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('name', '=', 'Assembly')], limit=1)
        location_pending_id = self.env['stock.location'].with_context(lang=None).search(
            [('usage', '=', 'internal'),
             ('name', '=', 'Pending'),
             ('location_id', '=', location_id.id)], limit=1)
        for pr in self:
            for prl in pr.production_record_line_ids:
                line = prl.assembly_panel_line_id
                if pr.assembly_section == u'框架':
                    if not line.frame_production_id:
                        for bl in line.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                            line.frame_production_id = self.env['mrp.production'].sudo().create({
                                'bom_id': bl.line_bom_id.id,
                                'product_id': bl.line_bom_id.product_id.id,
                                'product_uom_id': bl.line_bom_id.product_id.uom_id.id,
                                'product_qty': prl.prepared_qty,
                                'location_src_id': location_pending_id.id,
                                'location_dest_id': location_pending_id.id,
                            })
                    else:
                        qty_wizard = self.env['change.production.qty'].sudo().create({
                            'mo_id': line.frame_production_id.id,
                            'product_qty': prl.prepared_qty,
                        })
                        line.frame_production_id.do_unreserve()
                        qty_wizard.change_prod_qty()

                    line.frame_production_id.action_assign()

                    if prl.assembly_qty > 0:
                        produce_wizard = self.env['mrp.product.produce'].sudo().with_context({
                            'active_id': line.frame_production_id.id,
                            'active_ids': [line.frame_production_id.id],
                        }).create({
                            'product_qty': prl.assembly_qty,
                        })
                        produce_wizard.do_produce()
                    if line.frame_production_id.post_visible:
                        line.frame_production_id.post_inventory()

                else:
                    if not line.production_id:
                        line.production_id = self.env['mrp.production'].sudo().create({
                            'bom_id': line.bom_id.id,
                            'product_id': line.bom_id.product_id.id,
                            'product_uom_id': line.bom_id.product_id.uom_id.id,
                            'product_qty': line.completed_prep,
                            'location_src_id': location_pending_id.id,
                            'location_dest_id': location_pending_id.id,
                        })
                    else:
                        qty_wizard = self.env['change.production.qty'].sudo().create({
                            'mo_id': line.production_id.id,
                            'product_qty': line.frame_completed_prep,
                        })
                        line.production_id.do_unreserve()
                        qty_wizard.change_prod_qty()

                    line.production_id.action_assign()

                    if prl.assembly_qty > 0:
                        produce_wizard = self.env['mrp.product.produce'].sudo().with_context({
                            'active_id': line.production_id.id,
                            'active_ids': [line.production_id.id],
                        }).create({
                            'product_qty': prl.assembly_qty,
                        })
                        produce_wizard.do_produce()
                    if line.production_id.post_visible:
                        line.production_id.post_inventory()

    @api.multi
    def act_cancel(self):
        self.write({'state': 'cancel'})

    @api.onchange('assembly_section')
    def onchange_assembly_section(self):
        self.production_record_line_ids = []

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tokiku.production_record') or '/'

        return super(ProductionRecord, self).create(vals)

    @api.multi
    def _compute_order_num(self):
        for o in self:
            o.order_num = '%s-%s-%s-%s' % (o.name[:2], o.factory_id.supplier_id.ref, o.assembly_section, o.name[2:])

    @api.multi
    def item_select(self):
        self.ensure_one()
        project_id = self.env.context.get('default_project_id')
        panel_id = self.env.context.get('panel_id')

        ctx = {'default_project_id': project_id,
               'assembly_section': self.assembly_section,
               'panel_id': panel_id,
               'production_record_id': self.id
               }

        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'production_record_select_wizard_view')[1]

        return {
            'name': _('Production Record Select Wizard'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.production_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

    @api.multi
    def act_produce(self):
        for rec in self:
            for production in rec.production_ids:
                p = production.open_produce_product
                print ("p %s" % p)
                p.do_produce


class ProductionRecordLine(models.Model):
    _name = 'tokiku.production_record_line'

    name = fields.Char(string='Part Number')
    assembly_panel_line_id = fields.Many2one('tokiku.assembly_panel_line')
    production_record_id = fields.Many2one('tokiku.production_record', string='Production Record',
                                           ondelete='cascade')
    # partner_id = fields.Many2one('res.partner')
    # building = fields.Char(string='building')
    building_id = fields.Many2one('tokiku.building', string='Building')  # 棟別
    # atlas_id = fields.Many2one('tokiku.atlas', string='Processing Atlas')
    atlas_id = fields.Many2one('tokiku.atlas', 'Atlas')
    bom_id = fields.Many2one('mrp.bom', string='BOM Number')

    prepared_qty = fields.Integer(string='Prepared Qty')  # 備料完成數(手填)
    ready_qty = fields.Integer(string='Ready Qty', compute='_compute_ready_qty')  # 備料已完成
    estimated_qty = fields.Integer(string='Estimated Qty', compute='_compute_estimated_qty')  # 預定可組數
    queue_qty = fields.Integer(string='Queue Qty', compute='_compute_queue_qty')  # 未上架數
    shelf_qty = fields.Integer(string='Shelf Qty')  # 上架數(手填)
    assembling_qty = fields.Integer(string='Assembling Qty', compute='_compute_queue_qty')  # 未上架數
    assembly_qty = fields.Integer(string='Assembly Qty')  # 組裝數量(手填)
    assembled_qty = fields.Integer(string='Assembled Qty', compute='_compute_assembled_qty')  # 組裝已完成
    run_date = fields.Date(string='Run Date', related='production_record_id.run_date', store=True)


    @api.multi
    def _compute_ready_qty(self):
        for l in self:
            if l.production_record_id.assembly_section == u'框架':
                l.ready_qty = l.assembly_panel_line_id.frame_completed_prep
            else:
                l.ready_qty = l.assembly_panel_line_id.completed_prep

    @api.multi
    def _compute_estimated_qty(self):
        for l in self:
            if l.production_record_id.assembly_section == u'框架':
                l.estimated_qty = l.assembly_panel_line_id.frame_scheduled_assembly_qty
            else:
                l.estimated_qty = l.assembly_panel_line_id.scheduled_assembly_qty

    @api.multi
    def _compute_queue_qty(self):
        for l in self:
            assigned_qty = 0
            for ol in l.assembly_panel_line_id.assembly_order_line_ids.filtered(
                    lambda x: x.assembly_order_id.assembly_section == l.production_record_id.assembly_section and x.assembly_order_id.state == 'done' and x.run_date == datetime.today().strftime("%Y-%m-%d")):
                assigned_qty += ol.assembly_qty

            shelf_qty = 0
            assembly_qty = 0
            for pl in l.assembly_panel_line_id.production_record_line_ids.filtered(
                    lambda  x: x.production_record_id.assembly_section == l.production_record_id.assembly_section and x.production_record_id.state == 'done' and x.run_date == datetime.today().strftime("%Y-%m-%d")):
                shelf_qty += pl.shelf_qty
                assembly_qty += pl.assembly_qty

            l.queue_qty = assigned_qty - shelf_qty
            l.assembling_qty = shelf_qty - assembly_qty

    @api.multi
    def _compute_assembled_qty(self):
        for l in self:
            if l.production_record_id.assembly_section == u'框架':
                l.assembled_qty = l.assembly_panel_line_id.frame_assembled
            else:
                l.assembled_qty = l.assembly_panel_line_id.assembled
