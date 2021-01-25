# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TokikuBom(models.Model):
    """ Defines bills of material for a product or a product template """
    # _name = 'tokiku.bom'
    _description = 'Bill of Material'
    _inherit = ['mrp.bom']

    # contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project')
    atlas_id = fields.Many2one('tokiku.atlas', 'Atlas')
    assembly_panel_line_ids = fields.One2many('tokiku.assembly_panel_line', 'bom_id')
    assembly_po_line_ids = fields.One2many('purchase.order.line', 'bom_id')
    line_id = fields.One2many('mrp.bom.line', 'line_bom_id')

    # name = fields.Many2one('tokiku.atlas_line.name')
    # assembly_section = fields.Many2one('tokiku.atlas_line.assembly_section')

    @api.multi
    def name_get(self):
        return [(bom.id, bom.product_id.name or bom.product_tmpl_id.display_name) for bom in self]


class MrpBomLine(models.Model):
    # _name = 'tokiku.bom.line'
    _inherit = ['mrp.bom.line']

    line_bom_id = fields.Many2one('mrp.bom', delete='casecade')
    default_code = fields.Char(related='product_id.default_code', string='Processing Number')
    panel_line_id = fields.Many2one('tokiku.panel_line', compute='_compute_panel_line_id')
    assembly_section = fields.Char(string='Assembly Section', related='panel_line_id.assembly_section')
    shared_mat_demand = fields.Integer(string='Shared Material Demand',
                                       related='panel_line_id.demand_qty')  # 共用料總需求
    atlas_order_qty = fields.Integer(string='Atlas Order Qty',
                                     related='panel_line_id.total_ordered_qty')  # 圖集總下單數
    atlas_rest_demand_qty = fields.Integer(string='Atlas No Order Qty',
                                           related='panel_line_id.rest_demand_qty')  # 圖集未下訂數

    qty_demand = fields.Float(string='Demand Qty', compute='_compute_qty_demand', digits=(16, 0))
    qty_stock = fields.Float(string='TKK Inventory', related='panel_line_id.qty_stock', digits=(16, 0))  # 東菊總倉
    qty_refined = fields.Float(string='Refined Qty', related='panel_line_id.refined_qty',
                               digits=(16, 0))  # 加工廠(數量)
    qty_heat = fields.Integer(string='Heat Qty', related='panel_line_id.qty_heat')  # 熱處理廠(數量)
    qty_paint = fields.Integer(string='Paint Qty', related='panel_line_id.qty_paint')  # 烤漆場(數量)
    qty_assembly = fields.Integer(string='Assembly Qty', related='panel_line_id.qty_receive_assembly', store=True)

    @api.multi
    @api.depends('line_bom_id')
    def _compute_qty_demand(self):
        for l in self:
            l.qty_demand = self.env.context.get('total_demand') * l.product_qty

    @api.multi
    @api.depends('line_bom_id')
    def _compute_panel_line_id(self):
        for l in self:
            atlas_id = self.env.context.get('atlas_id')
            if not atlas_id:
                for pl in l.bom_id.assembly_panel_line_ids:
                    atlas_id = pl.atlas_id.id
                    break

            if not atlas_id:
                for pl in l.bom_id.line_id.bom_id.assembly_panel_line_ids:
                    atlas_id = pl.atlas_id.id
                    break

            l.panel_line_id = self.env['tokiku.panel_line'].search(
                [('atlas_id', '=', atlas_id),
                 ('product_id', '=', l.product_id.id), ], limit=1)


# class MrpProduction(models.Model):
#     """ Manufacturing Orders """
#     _inherit = 'mrp.production'
#
#     # quantity_demand = fields.Float('Quantity Demand', digits=(16, 0))
#     quantity_available = fields.Float('Quantity Available', digits=(16, 0))

    # assembly_panel_line_id = fields.Many2one('tokiku.assembly_panel_line', delete='cascade')

    # frame_assembly_panel_line_ids = fields.One2many('tokiku.assembly_panel_line', 'frame_mo_id')

    # @api.multi
    # def action_assign(self):
    #     res = super(MrpProduction, self).action_assign()
    #     for production in self:
    #         quantity_available = production.quantity_demand
    #         for mr in production.move_raw_ids:
    #             qa = mr.quantity_available / mr.unit_factor
    #             if qa < quantity_available:
    #                 quantity_available = qa
    #         production.quantity_available = quantity_available
    #         # print mr.quantity_done_store
    #         # print mr.quantity_done
    #     return res

    # building = fields.Char(string='Building')
    # contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    # categ_id = fields.Many2one('product.category', 'Category')
    # atlas_id = fields.Many2one('tokiku.atlas', 'Atlas')
    # assembled_qty = fields.Integer('Assembled Quantity', compute='_compute_assembled_qty')
    # shortage_qty = fields.Integer('Shortage Quantity', compute='_compute_assembled_qty')
    # partner_id = fields.Many2one('res.partner', string='Assembly Factory', change_default=False)
    #
    #
    # # Preparation
    # frame_assemable_qty = fields.Integer(string='Frame Assemable Qty')  # 框架預定可組數
    # frame_preparation_ok_qty = fields.Integer(string='Frame Preparation Ok Qty')  # 框架備料已完成
    # frame_not_preparation_qty = fields.Integer(string='Frame Not Preparation Qty')  # 框架備料未備數
    #
    # surface_assemable_qty = fields.Integer(string='Surface Assemable Qty')  # 框面預定可組數
    # surface_preparation_ok_qty = fields.Integer(string='Surface Preparation Ok Qty')  # 框面備料已完成
    # surface_not_preparation_qty = fields.Integer(string='Surface Not Preparation Qty')  # 框面備料未備數
    #
    # # Assembly
    # # 單元編號(BOM) bom
    # # 尺寸Ｗ width = fields.Float()
    # # 尺寸Ｈ height = fields.Float()
    # # 單一面積 area = fields.Float()
    # # 型式說明
    # # 總需求數量
    # # ordered_qty = fields.Integer()#下單數量
    # # not_ordered_qty = fields.Integer() #未下單數量
    #
    # # [框架組立]
    # # 備料完成 surface_preparation_ok_qty 上面有
    # frame_assembling_qty = fields.Integer(string='Frame Assembling Qty')  # 組立中
    # frame_assemble_ok_qty = fields.Integer(string='Frame Assemble Ok Qty')  # 組立完成
    # frame_not_assemable_qty = fields.Integer(string='Frame Not Assemable Qty')  # 未組裝
    #
    # # [面材組立]
    # surface_assembling_qty = fields.Integer(string='Surface Assembling Qty')  # 組立中
    # surface_assemble_ok_qty = fields.Integer(string='Surface Assemble Ok Qty')  # 組立完成
    # surface_not_assemble_qty = fields.Integer(string='Surface Not Assemble Qty')  # 未完成
    #
    # # [出貨]
    # shelf_packaging_qty = fields.Integer(string='Shelf Packaging Qty')  # 上架包裝
    # shipped_qty = fields.Integer(string='Shipped Qty')  # 出貨完成
    # not_ship_qty = fields.Integer(string='Not Ship Qty')  # 未出貨
    # wait_to_ship = fields.Integer(string='Wait To Ship')  # 待出貨
    #
    # remark = fields.Char(string='Remark')  # 備註
    #
    # @api.multi
    # def act_detail(self):
    #     view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_preparation_order_line_tree')[1]
    #
    #     return {
    #         'name': 'Panel Not Purchase Table',
    #         'view_type': 'tree',
    #         'view_mode': 'tree',
    #         'res_model': 'tokiku.preparation_order_line',
    #         # 'res_id': self.id,
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id,
    #         'target': 'current',
    #         'flags': {'form': {'action_buttons': True}, 'default_view': view_id},
    #         # 'context': {'default_categ_id': categ.id, 'default_contract_id': self.id}
    #     }
    #
    # @api.multi
    # def _compute_assembled_qty(self):
    #     for m in self:
    #         assembled_qty = 0
    #         shortage_qty = 0
    #         for raw in m.move_raw_ids:
    #             qty = (raw.quantity_done + raw.quantity_available) / raw.product_uom_qty
    #             if qty < 1:
    #                 shortage_qty += 1
    #             if assembled_qty == 0 or assembled_qty > int(qty):
    #                 assembled_qty = int(qty)
    #         m.assembled_qty = assembled_qty * m.product_qty
    #         m.shortage_qty = shortage_qty

    # @api.onchange('contract_id')
    # def _onchange_contract_id(self):
    #     categ_id = self.categ_id.id
    #     if self.contract_id:
    #         proj_id = self.contract_id.project_id.id
    #         if proj_id and categ_id:
    #             prod_ids = self.env['product.product'].search(
    #                 [('categ_id', '=', categ_id), ('project_id', '=', proj_id)])
    #             return {'domain': {'product_id': [('id', 'in', [prod.id for prod in prod_ids])]}}
    #
    #     return {}
    #
    # @api.onchange('picking_type_id')
    # def onchange_picking_type(self):
    #     location = self.env.ref('stock.stock_location_stock')
    #     location_src_id = self._context.get('default_location_src_id')
    #     location_dest_id = self._context.get('default_location_dest_id')
    #     self.location_src_id = location_src_id or self.picking_type_id.default_location_src_id.id or location.id
    #     self.location_dest_id = location_dest_id or self.picking_type_id.default_location_dest_id.id or location.id
