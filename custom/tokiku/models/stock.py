# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from core.biznavi.utils import parse_str
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    partner_id = fields.Many2one('res.partner')
    panel_line_id = fields.Many2one('tokiku.panel_line', compute='_compute_panel_line', store=True)

    @api.multi
    @api.depends('history_ids', 'history_ids.panel_line_id')
    def _compute_panel_line(self):
        for quant in self:
            for h in quant.history_ids:
                quant.panel_line_id = h.panel_line_id
                break

    def _quant_create_from_move(self, qty, move, lot_id=False, owner_id=False, src_package_id=False,
                                dest_package_id=False, force_location_from=False, force_location_to=False):
        price_unit = move.get_price_unit()
        location = force_location_to or move.location_dest_id
        rounding = move.product_id.uom_id.rounding
        partner_id = move.picking_id.partner_id.id or owner_id

        vals = {
            'product_id': move.product_id.id,
            'location_id': location.id,
            'qty': float_round(qty, precision_rounding=rounding),
            'cost': price_unit,
            'history_ids': [(4, move.id)],
            'in_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'company_id': move.company_id.id,
            'lot_id': lot_id,
            'owner_id': owner_id,
            'partner_id': owner_id,
            # 'package_id': dest_pkg.id,
            'package_id': dest_package_id,
        }
        if move.location_id.usage == 'internal':
            # if we were trying to move something from an internal location and reach here (quant creation),
            # it means that a negative quant has to be created as well.
            negative_vals = vals.copy()
            negative_vals['location_id'] = force_location_from and force_location_from.id or move.location_id.id
            negative_vals['qty'] = float_round(-qty, precision_rounding=rounding)
            negative_vals['cost'] = price_unit
            negative_vals['negative_move_id'] = move.id
            negative_vals['package_id'] = src_package_id
            # negative_vals['package_id'] = dest_pkg.id
            negative_vals['partner_id'] = partner_id
            negative_quant_id = self.sudo().create(negative_vals)
            vals.update({'propagated_from_id': negative_quant_id.id})

        picking_type = move.picking_id and move.picking_id.picking_type_id or False
        if lot_id and move.product_id.tracking == 'serial' and (
                not picking_type or (picking_type.use_create_lots or picking_type.use_existing_lots)):
            if qty != 1.0:
                raise UserError(_('You should only receive by the piece with the same serial number'))

        # create the quant as superuser, because we want to restrict the creation of quant manually: we should always use this method to create quants
        return self.sudo().create(vals)


class StockPicking(models.Model):

    _inherit = 'stock.picking'


    def _get_project_id(self):
        return self.env.user.project_id

    categ_id = fields.Many2one('product.category', 'Category')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project', default=_get_project_id)
    stage = fields.Char('Processing Stage Category')
    atlas_ids = fields.Many2many('tokiku.atlas', string='Processing Atlas')
    # qty_done = fields.Float('Done', default=0.0)

    @api.multi
    def action_assign(self):
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))

        moves.action_assign()

        for m in moves:
            for op in m.linked_move_operation_ids:
                op.operation_id.write({
                    'owner_id': m.picking_id.owner_id.id,
                })

        return True
#新增倉儲
    @api.multi
    def open_stock_pick(self):
        if not self.env.user.contract_id:
            raise UserError(_('Please select a contract first!'))
            return

        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'vpicktree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_picking_form')[1]

        return {
            'name': _('Stock Operations'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.picking',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('project_id', '=', self.env.user.project_id.id)],
            'context': {'default_project_id': self.env.user.project_id.id,
                        'supplier_ids': [s.supplier_id.id for s in self.env.user.project_id.supplier_info_ids],
                        'contract_ids': [c.id for c in self.env.user.project_id.contract_ids],
                        'search_default_done': 1
                        }
        }

    def picking_product_select(self):
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_picking_product_select')[1]
        return {
            'name': _('Select'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.picking_product_select',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'picking_id': self.id,
                'default_supplier_id': self.partner_id.id,
                'display_default_code': False,
            }
        }

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        # self.owner_id = None
        stage = self.env.context.get('default_stage') or self.stage

        if stage:
            project_id = self.env.user.project_id.id or self.project_id.id
            location_name = self.location_dest_id.with_context(lang=None).location_id.name or ''
            if location_name == 'Site':
                location_name = 'Installation'
            supplier_infos = self.env['tokiku.supplier_info'].search(
                [('project_id', '=', project_id),
                 ('prod_catg.code', '=', location_name.lower())])

            return {'domain': {'owner_id': [('id', 'in', [s.supplier_id.id for s in supplier_infos])]}}

    @api.onchange('location_id')
    def onchange_location_id(self):
        location_dest_ids = self.env.context.get('location_dest_ids')
        if self.env.context.get('location_site_id'):
            # location_dest_ids.append(self.env.context.get('location_site_id'))
            if self.location_id.id in location_dest_ids:
                location_dest_ids.remove(self.location_id.id)
            if self.location_id.with_context(lang=None).name == 'Pending':
                self.location_dest_id = self.env.context.get('location_done_id')
            else:
                if self.location_id.location_id.with_context(lang=None).name == 'Assembly':
                    self.location_dest_id = self.env.context.get('location_site_id')
                else:
                    self.location_dest_id = self.env.context.get('location_next_id')

            return {'domain': {'location_dest_id': [('id', 'in', location_dest_ids)]}}

    @api.onchange('partner_id', 'location_id', 'location_dest_id', 'picking_type_id')
    def onchange_picking_type(self):
        project_id = self.env.user.project_id.id or self.project_id.id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
    #     self.env.context = self.with_context(display_default_code=False).env.context
    #     # stage = self.env.context.get('default_stage') or self.stage
    #
    #     # pkg = self.env['stock.quant.package']
    #     # pend_pkg = pkg.search([('name', '=', u'待加工')])
    #     # done_pkg = pkg.search([('name', '=', u'已加工待出貨')])
    #
        quants = self.env['stock.quant'].search(
            [('location_id', '=', self.location_id.id),  # ('partner_id', '!=', False),
             ('product_id.project_id', '=', project_id),
             ('product_id.categ_id.panel_categ_id', '=', categ_id),
             # ('panel_line_id.atlas_id', 'in', [s.id for s in self.atlas_ids])
             ])
    #
    #     # if stage == 'ship':
    #     #     quants = self.env['stock.quant'].search(
    #     #         [('location_id', '=', self.location_id.id), ('package_id', '=', False),
    #     #          ('product_id.project_id', '=', project_id), ('product_id.categ_id', '=', categ_id)])
    #     # else:
    #     #     quants = self.env['stock.quant'].search(
    #     #         [('location_id', '=', self.location_id.id), ('package_id', '!=', False),
    #     #          ('product_id.project_id', '=', project_id), ('product_id.categ_id', '=', categ_id)])
    #
    #     #print [x.id for x in quants]
    #     mls = []
        partner_ids = []
    #     qtys = {}
    #     product_ids = {}
    #     src_partner_ids = {}
    #     panel_ids = {}
    #     # for q in quants:
    #     #     if q.partner_id.id not in partner_ids:
    #     #         partner_ids.append(q.partner_id.id)
    #     #     for mv in q.history_ids.filtered(lambda x: x.location_id.id == q.location_id.id or x.location_dest_id.id == q.location_id.id):
    #     #         group_key = "%s/%s/%s" % (q.product_id.id, q.partner_id.id, mv.atlas_id.id)
    #     #         prod_qty = mv.product_uom_qty
    #     #         if mv.location_id.id == q.location_id.id:
    #     #             prod_qty = (prod_qty * -1)
    #     #         if group_key in qtys:
    #     #             qtys[group_key] += prod_qty
    #     #         else:
    #     #             panel_ids[group_key] = mv.panel_line_id
    #     #             qtys[group_key] = prod_qty
    #     #             product_ids[group_key] = q.product_id
    #     #             src_partner_ids[group_key] = q.partner_id.id
    #
        for q in quants:
            if q.partner_id.id not in partner_ids:
                partner_ids.append(q.partner_id.id)
    #
    #         #group_key = "%s/%s/%s" % (q.product_id.id, q.partner_id.id, q.history_ids[0].atlas_id.id)
    #         #if group_key in qtys:
    #             #qtys[group_key] += q.qty
    #
    #         group_key = "%s/%s" % (q.product_id.id,q.history_ids[0].atlas_id.id)
    #         if group_key in qtys:
    #             qtys[group_key] += q.qty
    #
    #         else:
    #             qtys[group_key] = q.qty
    #             panel_ids[group_key] = q.history_ids[0].panel_line_id
    #             product_ids[group_key] = q.product_id
    #             src_partner_ids[group_key] = q.partner_id.id
    #             # pkg_ids[group_key] = q.package_id.id
    #
    #     location_name = self.location_dest_id.location_id.with_context(lang=None).name
    #     for k in qtys:
    #         if src_partner_ids[k] == self.partner_id.id and qtys[k] > 0:
    #             # and (not pkg_ids[k] or pkg_ids[k] == pkg_id):
    #             tmp_coating = panel_ids[k].surface_coating or ''
    #             tmp_heating = panel_ids[k].heating or ''
    #
    #             if location_name in ['Refine', 'Assembly'] or (
    #                     location_name == 'Heat' and len(parse_str(tmp_heating).replace("'", "")) > 0) or (
    #                     location_name == 'Paint' and len(parse_str(tmp_coating).replace("'", "")) > 0):
    #                 mls.append((0, 0, {
    #                     'name': product_ids[k].name,
    #                     'panel_line_id': panel_ids[k].id,
    #                     'date': datetime.now(),
    #                     'company_id': self.env['res.company']._company_default_get('stock.move'),
    #                     'date_expected': datetime.now(),
    #                     'product_id': product_ids[k].id,
    #                     'product_uom': product_ids[k].uom_id.id,
    #                     'product_uom_qty': qtys[k],
    #                     'location_id': self.location_id.id,
    #                     'location_dest_id': self.location_dest_id.id,
    #                     'owner_id': src_partner_ids[k],
    #                     'procure_method': 'make_to_stock',
    #                     'state': 'draft',
    #                 }))
    #     # print ("move line %s" % mls)
    #
    #     self.move_lines = mls
    #
        return {'domain': {'partner_id': [('id', 'in', partner_ids)]}}

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        project_id = self.env.user.project_id.id or self.project_id.id
        categ_id = self.env.context.get('default_categ_id') or self.categ_id.id
        self.env.context = self.with_context(display_default_code=False).env.context
        # stage = self.env.context.get('default_stage') or self.stage

        # pkg = self.env['stock.quant.package']
        # pend_pkg = pkg.search([('name', '=', u'待加工')])
        # done_pkg = pkg.search([('name', '=', u'已加工待出貨')])

        domain = [('location_id', '=', res.location_id.id),  # ('partner_id', '!=', False),
                  ('product_id.project_id', '=', project_id),
                  ('product_id.categ_id.panel_categ_id', '=', categ_id),
                  ]
        if vals.get('atlas_ids', False):
            domain.append(('panel_line_id.atlas_id', 'in', vals.get('atlas_ids')[0][2]))

        quants = self.env['stock.quant'].search(domain)

        mls = []
        partner_ids = []
        qtys = {}
        product_ids = {}
        src_partner_ids = {}
        panel_ids = {}

        for q in quants:
            if q.partner_id.id not in partner_ids:
                partner_ids.append(q.partner_id.id)

            group_key = "%s/%s" % (q.product_id.id, q.history_ids[0].atlas_id.id)
            if group_key in qtys:
                qtys[group_key] += q.qty

            else:
                qtys[group_key] = q.qty
                panel_ids[group_key] = q.history_ids[0].panel_line_id
                product_ids[group_key] = q.product_id
                src_partner_ids[group_key] = q.partner_id.id

        location_name = res.location_dest_id.location_id.with_context(lang=None).name
        print location_name
        for k in qtys:
            if src_partner_ids[k] == res.partner_id.id and qtys[k] > 0:
                tmp_coating = panel_ids[k].surface_coating or ''
                tmp_heating = panel_ids[k].heating or ''

                if location_name in ['Refine', 'Assembly', 'Site', 'Paint', 'Heat'] or (
                        location_name == 'Heat' and len(parse_str(tmp_heating).replace("'", "")) > 0) or (
                        location_name == 'Paint' and len(parse_str(tmp_coating).replace("'", "")) > 0):
                    mls.append((0, 0, {
                        'name': product_ids[k].name,
                        'panel_line_id': panel_ids[k].id,
                        'date': datetime.now(),
                        'company_id': self.env['res.company']._company_default_get('stock.move'),
                        'date_expected': datetime.now(),
                        'product_id': product_ids[k].id,
                        'product_uom': product_ids[k].uom_id.id,
                        'product_uom_qty': qtys[k],
                        'location_id': res.location_id.id,
                        'location_dest_id': res.location_dest_id.id,
                        'owner_id': src_partner_ids[k],
                        'procure_method': 'make_to_stock',
                        'state': 'draft',
                    }))
        print ("move line %s" % mls)

        res.move_lines = mls
        return res

    @api.multi
    def write(self, vals):
        result = super(StockPicking, self).write(vals)
        for rec in self:
            for ml in rec.move_lines:
                panel_id = ml.panel_line_id.panel_id
                if not panel_id:
                    panel_id = self.env['tokiku.panel'].search(
                        [('project_id', '=', rec.project_id.id), ('categ_id', '=', rec.categ_id.id)])
                # if len(rec.pack_operation_product_ids) > 0 and rec.state in ['done', 'cancel']:
                #     panel_id.cal_stock()
                # panel_id.refresh = True
                ml.panel_line_id._compute_qty_received()
                ml.panel_line_id._compute_rest_demand_qty()
                ml.panel_line_id._compute_weight()
                ml.panel_line_id._compute_weight_sub()

                ml.panel_line_id._compute_paint_qty()
                ml.panel_line_id._compute_cutdone_qty()
                ml.panel_line_id._compute_refined_pending_qty()
                ml.panel_line_id._compute_refined_qty()
                ml.panel_line_id._compute_refine_order_qty()
                ml.panel_line_id._compute_heat_qty()
                ml.panel_line_id._compute_paint_order_qty()
                ml.panel_line_id._compute_heat_order_qty()
                ml.panel_line_id._compute_qty_receive_site()
                ml.panel_line_id._compute_qty_receive_assembly()
                ml.panel_line_id._compute_percent()
                ml.panel_line_id._compute_area()

        return result

    def _prepare_pack_ops(self, quants, forced_qties):
        """ Prepare pack_operations, returns a list of dict to give at create """
        pack_operation_values = []
        for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):
            val_dict = {
                'picking_id': self.id,
                'product_qty': move.product_id.uom_id._compute_quantity(move.product_uom_qty, move.product_id.uom_id),
                'product_id': move.product_id.id,
                # 'package_id': move.,
                'owner_id': self.owner_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_uom_id': move.product_id.uom_id.id,
                'pack_lot_ids': [],
            }
            pack_operation_values.append(val_dict)

        # for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):
        #     values = product_id_to_vals.pop(move.product_id.id, [])
        #     pack_operation_values += values
        return pack_operation_values


class StockMove(models.Model):
    _inherit = "stock.move"

    atlas_id = fields.Many2one('tokiku.atlas', related='panel_line_id.atlas_id', string='Processing Atlas', store=True)
    panel_line_id = fields.Many2one('tokiku.panel_line', string="Panel Line")
    default_code = fields.Char(related='product_id.default_code', string='Processing Number', store=True)
    new_default_code = fields.Char(related='product_id.default_code', string='Part Number', store=True)
    code = fields.Char(string="Part Number", related='panel_line_id.code', store=True)
    product_name = fields.Char(related='product_id.name', string='Processing Number')
    categ_code = fields.Char(related='picking_id.categ_id.code', string='Category Code')
    parent_move_ids = fields.One2many('stock.move', related='production_id.move_finished_ids')
    # parent_move_id = fields.Many2one('stock.move')
    child_move_ids = fields.One2many('stock.move', compute='_compute_child_mo_ids')
    install_prodrec_line = fields.Many2one('tokiku.inst_prodrec_line', 'Install Product Rec', ondelete='set null', index=True, readonly=True)
    install_atlas = fields.Char(string='Install Atlas', compute='_compute_install_name', store=True)
    floor = fields.Char(string='Floor', compute='_compute_install_name', store=True)

    @api.multi
    @api.depends('install_prodrec_line.atlas_name', 'purchase_line_id.atlas_name')
    def _compute_install_name(self):
        for rec in self:
            for order in rec.purchase_line_id:
                rec.install_atlas = order.atlas_name
                rec.floor = order.floor
            for install in rec.install_prodrec_line:
                rec.install_atlas = install.atlas_name
    # material_panel_line_id = fields.Many2one('tokiku.panel_line', string="Panel Line", compute='_compute_panel_line_id')
    # assembly_section = fields.Char(string='Assembly Section', related='material_panel_line_id.assembly_section')
    # shared_mat_demand = fields.Integer(string='Shared Material Demand', related='material_panel_line_id.demand_qty')  # 共用料總需求
    # atlas_order_qty = fields.Integer(string='Atlas Order Qty', related='material_panel_line_id.total_ordered_qty')  # 圖集總下單數
    # atlas_rest_demand_qty = fields.Integer(string='Atlas No Order Qty',
    #                                        related='material_panel_line_id.rest_demand_qty')  # 圖集未下訂數
    #
    # qty_demand = fields.Float(string='Demand Qty', related='product_uom_qty', digits=(16, 0))
    # qty_stock = fields.Float(string='TKK Inventory', related='material_panel_line_id.qty_stock', digits=(16, 0))  # 東菊總倉
    # qty_refined = fields.Float(string='Refined Qty', related='material_panel_line_id.refined_qty', digits=(16, 0))  # 加工廠(數量)
    # qty_heat = fields.Integer(string='Heat Qty', related='material_panel_line_id.qty_heat')  # 熱處理廠(數量)
    # qty_paint = fields.Integer(string='Paint Qty', related='material_panel_line_id.qty_paint')  # 烤漆場(數量)
    # qty_assembly = fields.Integer(string='Assembly Qty', related='material_panel_line_id.qty_receive_assembly')  # 組裝廠(數量)

    # @api.multi
    # @api.depends('picking_id')
    # def _compute_panel_line_id(self):
    #     for m in self:
    #         panel_line_id = self.env['tokiku.panel_line'].search(
    #             [('atlas_id', '=', m.raw_material_production_id.assembly_panel_line_ids.atlas_id.id),
    #              ('product_id', '=', m.product_id.id), ])
    #         if not panel_line_id:
    #             panel_line_id = self.env['tokiku.panel_line'].search(
    #                 [('atlas_id', '=', m.raw_material_production_id.frame_assembly_panel_line_ids.atlas_id.id),
    #                  ('product_id', '=', m.product_id.id), ])
    #
    #         m.material_panel_line_id = panel_line_id

    @api.multi
    @api.depends('parent_move_ids')
    def _compute_child_mo_ids(self):
        for m in self:
            m.child_move_ids = self.env['mrp.production'].search([('product_id', '=', m.product_id.id)]).move_raw_ids


class PackOperation(models.Model):
    _inherit = "stock.pack.operation"
    _description = "Packing Operation"

    atlas_id = fields.Many2one('tokiku.atlas', string='Processing Atlas', compute="compute_atlas_id", store=True)
    default_code = fields.Char(related='product_id.default_code', string='Processing Number')
    new_default_code = fields.Char(related='product_id.default_code', string='Part Number', store=True)
    categ_code = fields.Char(related='picking_id.categ_id.code', string='Category Code')
    code = fields.Char(related='product_id.part_no', string='Default Code', store=True)

    ref_picking_name = fields.Char(related='picking_id.name', string='Reference')
    ref_partner_name = fields.Many2one(related='picking_id.partner_id', string='Partner')
    ref_min_date = fields.Datetime(related='picking_id.min_date', string='Scheduled Date')

    install_prodrec_line = fields.Many2one('tokiku.inst_prodrec_line')
    install_atlas = fields.Char(string='Atlas', compute="compute_atlas_id", store=True)
    floor = fields.Char(string='Floor', compute="compute_atlas_id", store=True)

    @api.multi
    @api.depends('linked_move_operation_ids.move_id.atlas_id',
                 'linked_move_operation_ids.move_id.purchase_line_id.atlas_name',
                 'install_prodrec_line.atlas_name')
    def compute_atlas_id(self):
        for op in self:
            for ml in op.linked_move_operation_ids:
                op.install_atlas = ml.move_id.purchase_line_id.atlas_name
                op.floor = ml.move_id.purchase_line_id.floor
                if ml.move_id.atlas_id:
                    op.atlas_id = ml.move_id.atlas_id
                    break
