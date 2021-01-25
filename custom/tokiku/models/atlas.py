# -*- coding: utf-8 -*-
import json
import math
import re
from datetime import datetime

import pytz

from core.biznavi.utils import parse_float, parse_str, parse_int
from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProcessingAtlas(models.Model):
    _name = 'tokiku.atlas'
    _description = 'Processing Atlas'
    _order = 'sequence, id'
    _rec_name = 'short_name'

    # @api.multi
    # def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,
    #                lazy=True):
    #
    #     res = super(ProcessingAtlas, self).read_group(cr, uid, domain, fields, groupby, offset, limit=limit,
    #                                             context=context, orderby=orderby, lazy=lazy)
    #     # if 'building' in fields:
    #     #     fields.remove('building')
    #     print (res)
    #     return res
    @api.multi
    def act_file_import(self):
        self.ensure_one()
        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_line_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_line_form')[1]

        return {
            'name': _('Atlas File Import'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.atlas_line',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_atlas_id': self.id
            },
            'domain': [
                ('atlas_id', '=', self.id)
            ]
        }

    @api.multi
    def act_imports(self):
        self.ensure_one()
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'new_version_atlas_view')[1]

        # last_atlas = self.env['tokiku.atlas'].search([('edit_atlas_id', '=', self.edit_atlas_id.id)], order="atlas_version desc",
        #                                              limit=1)
        if self.atlas_line_ids.filtered(lambda x: x.invalid_fields and len(x.invalid_fields) > 2):
            raise UserError(_('Please fix the invalid field before import!'))
            return

        design_change_ver = parse_str(self.edit_atlas_id.design_change_atlas_version)
        if not design_change_ver:
            ctx = {'atlas_id': self.id,
                   'default_design_change_atlas_version': ''}
        else:
            ctx = {'atlas_id': self.id,
                   'default_design_change_atlas_version': design_change_ver}

        return {
            'name': _('New Version Atlas Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.version_wizard',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

        # @api.multi
        # def act_import1(self):

        # self.create_new_version_atlas_reason()
        # print self.env.context.get('new_version_atlas_reason')

        # project_id = self.env.user.project_id
        # for a in self:
        #     products = []
        #     for p in a.atlas_line_ids:
        #         if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #             continue
        # if not p.bom_no or len(p.bom_no.strip()) == 0:
        #     continue
        # bom = self.env['mrp.bom'].sudo().search([('project_id', '=', project_id.id), ('product_id.default_code', '=', p.bom_no)], limit=1)
        # if not bom:
        #     bom_product = self.env['product.product'].sudo().search(
        #         [('name', '=', p.bom_no), ('project_id', '=', project_id.id), ('categ_id', '=', p.categ_id.id)],
        #         limit=1)
        #     if not bom_product:
        #         bom_product = self.env['product.product'].sudo().create({
        #             'project_id': project_id.id,
        #             'categ_id': p.categ_id.id,
        #             'name': p.bom_no,
        #             'default_code': p.bom_no,
        #             'type': 'product',
        #             # 'material': p.material_no
        #         })
        #     bom = self.env['mrp.bom'].sudo().create({
        #         'project_id': project_id.id,
        #         'product_tmpl_id': bom_product.product_tmpl_id.id,
        #         'product_id': bom_product.id,
        #         # 'product_qty': p.qty
        #     })
        # if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #     boms[bom.id] = [bom, parse_float(p.qty)]
        # else:

        #     product = self.env['product.product'].sudo().search(
        #         [('project_id', '=', project_id.id), ('default_code', '=', p.name)], limit=1)
        #     if product:
        #         products.append(product)
        #     if not product:
        #         product = self.env['product.product'].sudo().create({
        #             'project_id': project_id.id,
        #             'categ_id': p.categ_id.id,
        #             'name': parse_str(p.description),
        #             'default_code': parse_str(p.name),
        #             'type': 'product',
        #             # 'size': parse_str(p.cutting_length),
        #             'cutting_length': parse_float(p.cutting_length),
        #             'cutting_width': parse_float(p.cutting_width),
        #             'volume': parse_float(p.cutting_length) if p.categ_id.code == 'refine' else 0,
        #             # 'material': parse_str(p.material_no),
        #             'coating': parse_str(p.coating),
        #             'color_code': parse_str(p.color_code),
        #             'heating': parse_str(p.heating)
        #         })
        #         products.append(product)
        #
        # for code in ['refine', 'glass', 'plate', 'steel', 'iron', 'stone', 'accessories', 'others']:
        #     categ = self.env['product.category'].sudo().search([('code', '=', code)])
        #     panel = self.env['tokiku.panel'].sudo().search(
        #         [('contract_id', '=', a.contract_id.id), ('categ_id', '=', categ.id)])
        #     if not panel:
        #         panel = self.env['tokiku.panel'].sudo().create(
        #             {'contract_id': a.contract_id.id, 'categ_id': categ.id})
        # for p in a.production_ids.filtered(lambda x: x.product_id.categ_id.code == 'assembly'):
        #     for bl in p.bom_id.bom_line_ids.filtered(lambda x: x.product_id.categ_id.code == code):
        #         pl = panel.line_ids.filtered(lambda x: x.product_id.id == bl.product_id.id)
        #         if not pl:
        # print products
        #
        # for pd in products:
        #     if pd.category_code == code:
        #     # pl = panel.line_ids.filtered(lambda x: x.product_id.id == bl.product_id.id)
        #         _logger.info("=======================================")
        #         panel.sudo().line_ids = [(0, 0, {'product_id': pd.id, 'atlas_id': self.id})]
        #         # panel.compute_line_ids()

        # a.is_imported = False

        # bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == p.name)
        # if not bom_line:
        #     bom_line = self.env['mrp.bom.line'].sudo().create({
        #         'product_id': product.id,
        #         'product_qty': parse_float(p.unit_qty),
        #         'bom_id': bom.id
        #     })
        # bom_line.product_qty = parse_float(p.unit_qty)

        # ======line======
        #     if p.categ_id.code == 'refine':
        #         r_bom = self.env['mrp.bom'].sudo().search([('product_id.default_code', '=', p.name)], limit=1)
        #         if not r_bom:
        #             r_bom = self.env['mrp.bom'].sudo().create({
        #                 'product_tmpl_id': product.product_tmpl_id.id,
        #                 'product_id': product.id
        #             })
        #         boms[r_bom.id] = [r_bom, parse_float(p.qty)]
        #         r_bom_line = bom.bom_line_ids.filtered(
        #             lambda l: l.product_id.default_code == p.material_no.strip())

        # m_products = self.env['product.product'].sudo().search(
        #     [('default_code', '=', parse_str(p.material_no)), ('volume', '>', 0)])
        # min_rest = 0
        # l_product = None
        # l_qty = 0
        # for v in m_products:
        #     print "%s / %s" % (product.volume, v.volume)
        #     rest = (v.volume - 200) % product.volume
        #     if min_rest == 0 or min_rest > rest:
        #         min_rest = rest
        #         l_product = v
        #         l_qty = product.volume / (v.volume - 200 - rest)
        #
        # if l_product and not r_bom_line:
        #     r_bom_line = self.env['mrp.bom.line'].sudo().create({
        #         'product_id': l_product.id,
        #         'product_qty': l_qty,
        #         'bom_id': r_bom.id
        #     })
        # ======line======

        # production_ids = []
        # for i in boms:
        #     production_id = self.env['mrp.production'].sudo().search(
        #         [('contract_id', '=', p.atlas_id.contract_id.id), ('bom_id', '=', boms[i][0].id), ('atlas_id', '=', a.id)])
        #     location_src_id = self.env['stock.location'].with_context(lang=None).search(
        #         [('usage', '=', 'internal'), ('name', '=', 'Assembly')], limit=1)
        #     if not production_id:
        #         production_id = self.env['mrp.production'].sudo().create({
        #             'contract_id': p.atlas_id.contract_id.id,
        #             'bom_id': boms[i][0].id,
        #             'product_id': boms[i][0].product_id.id,
        #             'product_uom_id': boms[i][0].product_id.uom_id.id,
        #             'product_qty': boms[i][1],
        #             'atlas_id': a.id,
        #             'location_src_id': location_src_id.id,
        #         })
        #     for r in production_id:
        #         production_ids.append(r.id)
        # a.production_ids = [(6, 0, production_ids)]

    @api.multi
    def act_assembly_gen(self):
        project_id = self.env.user.project_id
        for a in self:
            if not a.partner_id:
                raise UserError(_('Please select an assembly partner first!'))
                return
            boms = {}

            # Check if BOM no. exists; if it doesn't exist, continue anyway
            line_insert = []
            categ = self.env['product.category'].sudo().search([('code', '=', "assembly")])
            panel = self.env['tokiku.panel'].sudo().search(
                [('project_id', '=', self.env.user.project_id.id),
                 ('categ_id', '=', categ.id)], limit=1)
            line_count = 0
            for al in a.atlas_line_ids:
                if not al.bom_no or len(al.bom_no.strip()) == 0 or parse_str(al.assembly_section) == u'不控管':
                    continue

                # Check if there are values in name, project_id, categ_id fields
                if al.panel_categ_id.id == categ.id:
                    bom_product = self.env['product.product'].sudo().search(
                        [('default_code', '=', al.bom_no.strip()),
                         ('project_id', '=', project_id.id),
                         # ('categ_id', '=', categ.id),
                         ], limit=1)

                    if not bom_product:
                        bom_product = self.env['product.product'].sudo().create({
                            'name': al.bom_no.strip(),
                            'default_code': al.bom_no.strip(),
                            'project_id': project_id.id,
                            'categ_id': categ.id,
                            'type': 'product'
                        })

                    bom = self.env['mrp.bom'].sudo().search([
                        ('project_id', '=', project_id.id),
                        ('product_id', '=', bom_product.id),
                        ('product_tmpl_id', '=', bom_product.product_tmpl_id.id),
                        ('atlas_id', '=', a.edit_atlas_id.id),
                    ], limit=1)

                    if not bom:
                        bom = self.env['mrp.bom'].sudo().create({
                            'project_id': project_id.id,
                            'product_id': bom_product.id,
                            'product_tmpl_id': bom_product.product_tmpl_id.id,
                            'atlas_id': a.edit_atlas_id.id,
                        })

                    # Checks whether the values in the below fields are empty in assembly_panel_line
                    building = False
                    if al.building and len(al.building.strip()) > 0:
                        building = self.env['tokiku.building'].search(
                            [('project_id', '=', project_id.id), ('name', '=', al.building.strip())], limit=1)

                        if not building:
                            building = self.env['tokiku.building'].create(
                                {'name': al.building.strip(), 'project_id': project_id.id})

                    line_count += 1
                    line = panel.sudo().assembly_panel_line_ids.filtered(
                        lambda l: l.bom_id.id == bom.id and l.atlas_id.id == a.edit_atlas_id.id and (
                                not building or l.building_id.id == building.id))

                    if not line:
                        line_insert.append((0, 0, {
                            'panel_id': panel.id,
                            'atlas_id': a.edit_atlas_id.id,
                            'building_id': building,
                            'supplier_id': a.edit_atlas_id.partner_id.id,
                            'bom_id': bom.id,
                            'total_demand': parse_int(al.qty),
                            'assembly_section': parse_str(al.assembly_section),
                            # 'mo_id': mo.id,
                        }))
                    else:
                        line.total_demand = parse_int(al.qty)
                        line.building_id = building
                        line.supplier_id = a.edit_atlas_id.partner_id.id
                        line.assembly_section = parse_str(al.assembly_section)
                        # if line.mo_id.product_qty != line.total_demand:
                        # self.change_prod_qty(line.mo_id, line.total_demand)

                elif al.name and al.bom_no:
                    bom_product = self.env['product.product'].sudo().search(
                        [('default_code', '=', al.bom_no.strip()),
                         ('project_id', '=', project_id.id),
                         # ('categ_id', '=', categ.id)
                         ], limit=1)

                    bom = self.env['mrp.bom'].sudo().search([
                        ('project_id', '=', project_id.id),
                        ('product_tmpl_id', '=', bom_product.product_tmpl_id.id),
                        ('atlas_id', '=', a.edit_atlas_id.id),
                    ], limit=1)

                    product = self.env['product.product'].sudo().search([
                        ('project_id', '=', project_id.id),
                        # ('categ_id', '=', al.categ_id.id),
                        ('default_code', '=', al.name.strip()),
                    ], limit=1)
                    if al.assembly_section.strip() in ['frame', u'框架']:
                        sub_bom_name = u'%s - 框架' % bom_product.default_code
                        sub_bom_product = self.env['product.product'].sudo().search(
                            [('name', '=', sub_bom_name),
                             ('default_code', '=', u'%s - 框架' % al.bom_no.strip()),
                             ('project_id', '=', project_id.id),
                             ('categ_id', '=', categ.id)
                             ], limit=1)
                        if not sub_bom_product:
                            sub_bom_product = self.env['product.product'].sudo().create({
                                'name': sub_bom_name,
                                'default_code': u'%s - 框架' % al.bom_no.strip(),
                                'project_id': project_id.id,
                                'categ_id': categ.id,
                                'type': 'product'
                            })
                        sub_bom = self.env['mrp.bom'].sudo().search([
                            ('project_id', '=', project_id.id),
                            ('product_tmpl_id', '=', sub_bom_product.product_tmpl_id.id),
                            ('atlas_id', '=', a.edit_atlas_id.id),
                        ], limit=1)
                        if not sub_bom:
                            sub_bom = self.env['mrp.bom'].sudo().create({
                                'project_id': project_id.id,
                                'product_tmpl_id': sub_bom_product.product_tmpl_id.id,
                                'product_id': sub_bom_product.id,
                                'atlas_id': a.edit_atlas_id.id,
                            })
                        sub_bom_line = sub_bom.bom_line_ids.filtered(
                            lambda l: l.product_id.default_code == al.name.strip())
                        if not sub_bom_line:
                            sub_bom_line = self.env['mrp.bom.line'].sudo().create({
                                'product_id': product.id,
                                'product_qty': parse_float(al.unit_qty),
                                'bom_id': sub_bom.id,
                            })
                        bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.id == sub_bom_product.id)
                        if not bom_line:
                            bom_line = self.env['mrp.bom.line'].sudo().create({
                                'product_id': sub_bom_product.id,
                                'product_qty': 1,
                                'bom_id': bom.id,
                                'line_bom_id': sub_bom.id,
                            })

                    else:
                        bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == al.name.strip())
                        if not bom_line:
                            bom_line = self.env['mrp.bom.line'].sudo().create({
                                'product_id': product.id,
                                'product_qty': parse_float(al.unit_qty),
                                'bom_id': bom.id
                            })

            if len(line_insert) > 0:
                panel.sudo().assembly_panel_line_ids = line_insert

            panel.sudo().assembly_panel_line_ids._compute_assembly_qty()
                # for l in panel.sudo().assembly_panel_line_ids:
                #     l.mo_id = self.env['mrp.production'].sudo().create({
                #         'bom_id': l.bom_id.id,
                #         'product_id': l.bom_id.product_id.id,
                #         'product_uom_id': l.bom_id.product_id.uom_id.id,
                #         'quantity_demand': l.total_demand,
                #         'product_qty': l.total_demand,
                #         'location_src_id': location_src_id.id,
                #         'location_dest_id': location_dest_id.id,
                #     })
                #     for bl in l.bom_id.bom_line_ids.filtered(lambda x: x.product_id.name.endswith(u' - 框架')):
                #         l.frame_mo_id = self.env['mrp.production'].sudo().create({
                #             'bom_id': bl.line_bom_id.id,
                #             'product_id': bl.line_bom_id.product_id.id,
                #             'product_uom_id': bl.line_bom_id.product_id.uom_id.id,
                #             'quantity_demand': l.total_demand,
                #             'product_qty': l.total_demand,
                #             'location_src_id': location_src_id.id,
                #             'location_dest_id': location_src_id.id,
                #         })

                # self.change_prod_qty(mo, parse_int(al.qty))

            msg = _('%d Panel Line imported.') % line_count
            ctx = dict(
                default_message=msg,
            )
            return {
                'name': _('Import Results'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'biznavi.msgbox',
                'target': 'new',
                'context': ctx,
            }

            #
            # production_ids = []
            #
            # categs = self.env['product.category'].sudo().search(
            #     [('code', 'in', ['assembly', 'assembly_preparation'])])
            # panels = self.env['tokiku.panel'].sudo().search(
            #     [('project_id', '=', self.env.user.project_id.id),
            #      ('categ_id', 'in', [c.id for c in categs])])
            #
            # for v in boms.itervalues():
            #     production_id = self.env['mrp.production'].sudo().search(
            #         [('contract_id', '=', a.contract_id.id),
            #          ('bom_id', '=', v['bom'].id),
            #          ('atlas_id', '=', a.edit_atlas_id.id),
            #          ('building', '=', v['building'])])
            #     location_src_id = self.env['stock.location'].with_context(lang=None).search(
            #         [('usage', '=', 'internal'),
            #          ('name', '=', 'Assembly')], limit=1)
            #     location_dest_id = self.env['stock.location'].with_context(lang=None).search(
            #         [('usage', '=', 'internal'),
            #          ('name', '=', 'Pending'),
            #          ('location_id', '=', location_src_id.id)], limit=1)
            #
            #     if not production_id:
            #         prod_obj = {
            #             'contract_id': al.atlas_id.contract_id.id,
            #             'bom_id': v['bom'].id,
            #             'product_id': v['bom'].product_id.id,
            #             'product_uom_id': v['bom'].product_id.uom_id.id,
            #             'product_qty': v['qty'],
            #             'atlas_id': a.edit_atlas_id.id,
            #             'location_src_id': location_src_id.id,
            #             'building': v['building'],
            #             'partner_id': a.partner_id.id
            #             # 'panel_ids': panel.id,
            #         }
            #
            #         default_code = v['bom'].product_id.default_code
            #         if default_code and ('frame' in default_code):
            #             prod_obj.update({'location_dest_id': location_dest_id.id})
            #         production_id = self.env['mrp.production'].sudo().create(prod_obj)
            #
            #     for r in production_id:
            #         production_ids.append(r.id)
            #
            #     a.production_ids = [(6, 0, production_ids)]
            #
            #     for p in panels:
            #         p.assembly_line_ids = [(6, 0, production_ids)]

    # @api.model
    # def change_prod_qty(self, production, product_qty):
    #     produced = sum(production.move_finished_ids.mapped('quantity_done'))
    #     if product_qty < produced:
    #         raise UserError(
    #             _("You have already processed %d. Please input a quantity higher than %d ") % (produced, produced))
    #     production.write({'product_qty': product_qty})
    #     done_moves = production.move_finished_ids.filtered(
    #         lambda x: x.state == 'done' and x.product_id == production.product_id)
    #     qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
    #                                                                   production.product_uom_id)
    #     factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced,
    #                                                          production.bom_id.product_uom_id) / production.bom_id.product_qty
    #     boms, lines = production.bom_id.explode(production.product_id, factor,
    #                                             picking_type=production.bom_id.picking_type_id)
    #     for line, line_data in lines:
    #         production._update_raw_move(line, line_data)
    #     operation_bom_qty = {}
    #     for bom, bom_data in boms:
    #         for operation in bom.routing_id.operation_ids:
    #             operation_bom_qty[operation.id] = bom_data['qty']
    #
    #     qty = production.product_qty - qty_produced
    #     production_move = production.move_finished_ids.filtered(
    #         lambda x: x.product_id.id == production.product_id.id and x.state not in ('done', 'cancel'))
    #     if production_move:
    #         production_move.write({'product_uom_qty': qty})
    #     else:
    #         production_move = production._generate_finished_moves()
    #         production_move = production.move_finished_ids.filtered(
    #             lambda x: x.state not in ('done', 'cancel') and production.product_id.id == x.product_id.id)
    #         production_move.write({'product_uom_qty': qty})
    #
    #     moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #     moves.do_unreserve()
    #     moves.action_assign()
    #     for wo in production.workorder_ids:
    #         operation = wo.operation_id
    #         if operation_bom_qty.get(operation.id):
    #             cycle_number = math.ceil(
    #                 operation_bom_qty[operation.id] / operation.workcenter_id.capacity)  # TODO: float_round UP
    #             wo.duration_expected = (operation.workcenter_id.time_start +
    #                                     operation.workcenter_id.time_stop +
    #                                     cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
    #         if production.product_id.tracking == 'serial':
    #             quantity = 1.0
    #         else:
    #             quantity = wo.qty_production - wo.qty_produced
    #             quantity = quantity if (quantity > 0) else 0
    #         wo.qty_producing = quantity
    #         if wo.qty_produced < wo.qty_production and wo.state == 'done':
    #             wo.state = 'progress'
    #         # assign moves; last operation receive all unassigned moves
    #         # TODO: following could be put in a function as it is similar as code in _workorders_create
    #         # TODO: only needed when creating new moves
    #         moves_raw = production.move_raw_ids.filtered(
    #             lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
    #         if wo == production.workorder_ids[-1]:
    #             moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
    #         moves_finished = production.move_finished_ids.filtered(
    #             lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
    #         moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
    #         (moves_finished + moves_raw).write({'workorder_id': wo.id})
    #         if wo.move_raw_ids.filtered(lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
    #             wo._generate_lot_ids()

    @api.onchange('contract_id')
    def _onchange_contract_item(self):
        _logger.info('_get_contract_item : %s' % self.contract_id.project_id)
        # sol_ids = self.env['sale.order.line'].search([('order_id.tokiku_project_id', '=', self.contract_id.project_id.id)])
        # _logger.info('_get_contract_item len: %s' % len(sol_ids))
        return {'domain': {'contract_id': [('id', 'in', [sol.id for sol in self.contract_id.project_id.contract_ids])]}}

    sequence = fields.Integer(default=1)
    name = fields.Char('Atlas', required=True)
    short_name = fields.Char('Short Name')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    project_id = fields.Many2one('project.project', string='Project', related='contract_id.project_id', store=True)
    file_date = fields.Date(string='File Date',
                            default=lambda self: datetime.now(pytz.timezone(self.env.user.partner_id.tz)).strftime(
                                '%Y-%m-%d'))
    atlas_line_ids = fields.One2many('tokiku.atlas_line', 'atlas_id', string='Atlas Line', copy=True)
    production_ids = fields.Many2many('mrp.production', string='Productions')

    partner_id = fields.Many2one('tokiku.supplier_info', string='Assembly Factory', change_default=False)

    is_imported = fields.Boolean("Is the atlas imported?", default=False)
    is_panel = fields.Boolean("Is the atlas has been put into panel?", default=False)
    is_production = fields.Boolean("Is the atlas production?", default=False)

    atlas_version = fields.Integer('Atlas Version', default=0, help="Atlas Version Control")
    design_change_atlas_version = fields.Char(string='Design Change Atlas Version')
    new_version_atlas_reason = fields.Char(string='New Version Atlas Reason')
    edit_atlas_id = fields.Many2one('tokiku.atlas', string='Edit Atlas')
    construction_section = fields.Many2one('tokiku.construction_section', string='Construction Section',
                                           ondelete='restrict')
    purchase_status = fields.Selection([('complete', 'Complete'),
                                        ('incomplete', 'Incomplete'), ])
    assembly_status = fields.Selection([('complete', 'Complete'),
                                        ('incomplete', 'Incomplete'), ])
    building = fields.Char()
    # default_code = fields.One2many('tokiku.panel_line', 'atlas_id', string='Part Number')
    # contract_item = fields.Many2one('sale.order.line', string='Contract Item')

    last_atlas_id = fields.Many2one('tokiku.atlas', compute='_compute_last_atlas_id')
    # last_write_date = fields.Datetime(related='last_atlas_id.write_date')
    # last_write_uid = fields.Many2one(related='last_atlas_id.write_uid')
    last_design_change_ver = fields.Char(related='last_atlas_id.design_change_atlas_version')
    last_purchase_status = fields.Selection(related='last_atlas_id.purchase_status')
    last_assembly_status = fields.Selection(related='last_atlas_id.assembly_status')
    last_atlas_version = fields.Integer(related='last_atlas_id.atlas_version')

    assembly_panel_line_ids = fields.One2many('tokiku.assembly_panel_line', 'atlas_id')
    # installation_panel_line_ids = fields.One2many('tokiku.installation_panel_line', 'atlas_id')
    # demand_line_ids = fields.One2many('tokiku.demand_line', 'atlas_id')

    @api.multi
    def _compute_last_atlas_id(self):
        for a in self:
            last_atlas = self.env['tokiku.atlas'].search(
                [('edit_atlas_id', '!=', False), ('edit_atlas_id', '=', a.edit_atlas_id.id)],
                order="atlas_version desc", limit=1)
            if len(last_atlas) > 0:
                a.last_atlas_id = last_atlas[0]

    @api.multi
    def check_demand_qty(self):
        bomDict = {}
        for a in self:
            for p in a.atlas_line_ids:
                if p.bom_no and len(p.bom_no) > 0 and (not p.name or p.name == '') and (
                        not p.description or p.description == ''):
                    if p.bom_no in bomDict.keys():
                        bomDict[p.bom_no] += int(p.qty)
                    else:
                        bomDict.update({p.bom_no: int(p.qty)})
                elif (not p.bom_no or p.bom_no == '') and (p.name and len(p.name) > 0) and (
                        p.unit_qty and len(p.unit_qty) > 0):
                    p.qty = p.unit_qty

        # Computes the sum of the Product Quantity (需求量) without Name (加工編號) and Product Unit Quantity (數量)
        for k in bomDict:
            for a in self:
                for p in a.atlas_line_ids:
                    if p.bom_no == k and p.name != '' and p.unit_qty != '':
                        compute_qty = bomDict[k] * int(p.unit_qty)
                        p.qty = str(compute_qty)

    @api.multi
    def write(self, vals):
        res = super(ProcessingAtlas, self).write(vals)
        bomDict = {}
        for a in self:
            for p in a.atlas_line_ids:
                if p.bom_no and len(p.bom_no) > 0 and (not p.name or p.name == '') and (
                        not p.description or p.description == ''):
                    if p.bom_no in bomDict.keys():
                        bomDict[p.bom_no] += parse_int(p.qty)
                    else:
                        bomDict.update({p.bom_no: parse_int(p.qty)})
                elif (not p.bom_no or p.bom_no == '') and (p.name and len(p.name) > 0) and (
                        p.unit_qty and len(p.unit_qty) > 0):
                    p.qty = p.unit_qty
        for k in bomDict:
            for a in self:
                for p in a.atlas_line_ids:
                    if p.bom_no == k and p.name != '' and p.unit_qty != '':
                        compute_qty = bomDict[k] * int(p.unit_qty)
                        p.qty = str(compute_qty)
        return res

    @api.model
    def create(self, vals):
        bomDict = {}
        for l in vals.get('atlas_line_ids'):
            p = l[2]
            if p.get('bom_no') != '' and p.get('name') == '' and p.get('description') == '':
                if p.get('bom_no') in bomDict.keys():
                    bomDict[p.get('bom_no')] += int(p['qty'])
                else:
                    bomDict.update({p['bom_no']: int(p['qty'])})
            elif p.get('bom_no') == '' and p.get('name') != '' and p.get('unit_qty') != '':
                p['qty'] = p['unit_qty']
        for k in bomDict:
            for l in vals.get('atlas_line_ids'):
                p = l[2]
                if p.get('bom_no') == k and p.get('name') != '' and p['unit_qty'] != '':
                    compute_qty = bomDict[k] * int(p['unit_qty'])
                    p['qty'] = str(compute_qty)
        res = super(ProcessingAtlas, self).create(vals)
        return res

    @api.multi
    def act_edit(self):
        self.ensure_one()
        # edit_atlas_id = self.env['tokiku.atlas'].search([('name', '=', self.name), ('contract_id', '=', self.env.user.contract_id.id), ('atlas_version', '=', 0)])
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_edit_form')[1]
        return {
            'name': _('Atlas'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.atlas',
            'view_id': form_id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'res_id': self.edit_atlas_id.id
        }

    @api.multi
    def open_atlas_history(self):
        self.ensure_one()
        tree_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_history_tree')[1]
        form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_form')[1]
        return {
            'name': _('Processing Atlas History'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.atlas',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [
                ('contract_id', '=', self.contract_id.id),
                ('edit_atlas_id', '=', self.edit_atlas_id.id),
                ('atlas_version', '>', 0)
            ]
        }


class ProcessingAtlasLine(models.Model):
    _name = 'tokiku.atlas_line'

    bom_no = fields.Char(string='BOM Number', default='')
    name = fields.Char(string='Processing Number', default='')
    code = fields.Char(string='Part Number', default='')
    cutting_length = fields.Char(string='Cutting Length', default='')
    cutting_width = fields.Char(string='Cutting Width', default='')

    description = fields.Char(string='Material Specification', default='')
    coating = fields.Char(string='Surface Coating', default='')
    color_code = fields.Char(string='Color Code', default='')
    heating = fields.Char(string='Heating', default='')

    unit_qty = fields.Char(string='Unit Quantity', default='')
    qty = fields.Char(string='Demand Quantity', default='')
    invalid_fields = fields.Char('Invalid Fields', compute='_compute_invalid_fields', store=False)
    atlas_id = fields.Many2one('tokiku.atlas', string='Demand', ondelete='cascade')
    categ_id = fields.Many2one('product.category', string='Category', compute='_compute_categ_id')
    categ_code = fields.Char(related='categ_id.code')
    panel_categ_id = fields.Many2one('product.category', string='Panel Category', related='categ_id.panel_categ_id')
    assembly_section = fields.Char(string='Assembly Section', default='')
    assembly_categ = fields.Many2one('product.category', string='Assembly Category', compute='_compute_assembly_categ')
    material = fields.Char(string='Material', default='')
    building = fields.Char(string='Building', default='')

    # 長寬單一面積型式說明
    frame_length = fields.Char(string='Frame Length', default='')
    frame_width = fields.Char(string='Frame Width', default='')
    frame_area = fields.Char(string='Frame Area', default='')
    frame_type_description = fields.Char(string='Frame Type Description', default='')


    @api.model
    def create(self, vals):
        for key, value in vals.iteritems():
            if not value:
                vals[key] = ''

        res = super(ProcessingAtlasLine, self).create(vals)
        return res

    # @api.multi
    # @api.depends('categ_id', 'description')
    # def _compute_material(self):
    #     for l in self:
    #         if l.categ_id.code == 'aluminum':
    #             if l.description:
    #                 desc_str = l.description
    #                 desc_str = ''.join(desc_str.split())  # remove all blanks
    #                 alum_idx = desc_str.find(u'鋁料')  # get index
    #                 if alum_idx >= 7:
    #                     l.material = desc_str[alum_idx - 7:alum_idx]  # get material

    @api.multi
    @api.depends('bom_no', 'name', 'description', 'code', 'unit_qty', 'qty')
    def _compute_categ_id(self):
        # All product category
        cats = self.env['product.category'].search([('parent_id', '!=', False)])
        assembly_cat = cats.filtered(lambda x: x.code == 'assembly')
        others_cat = cats.filtered(lambda x: x.code == 'others' and x.parent_id.code == 'material')
        for l in self:
            if l.bom_no and l.qty and len(parse_str(l.bom_no)) > 0 and len(parse_str(l.name)) == 0:
                l.categ_id = assembly_cat
                l.panel_categ_id = assembly_cat
            else:
                l.categ_id = others_cat
                l.panel_categ_id = others_cat
                p = 0
                for c in cats:
                    for k in c.keywords:
                        if l.description:
                            pos = l.description.find(k.name)
                            if pos >= p:
                                p = pos
                                l.categ_id = c
                                l.panel_categ_id = c

    @api.multi
    # @api.depends ('bom_no', 'name', 'assembly_section', 'code', 'unit_qty', 'qty')
    def _compute_assembly_categ(self):
        assembly_cats = self.env['product.category'].search([('parent_id.code', '=', 'assembly_section')])
        # print ("assembly_cats %s" % assembly_cats)
        for l in self:
            if l.bom_no and l.qty and len(parse_str(l.bom_no)) > 0 and len(parse_str(l.name)) == 0:
                continue
            else:
                p = 0
                if l.assembly_section:
                    for c in assembly_cats:
                        for k in c.keywords:
                            pos = l.assembly_section.find(k.name)
                            # print ("pos %s" % pos)
                            if pos >= p:
                                p = pos
                                l.assembly_categ = c
                                # print ("")

    # panel_cats = self.env['product.category'].search([('code', '!=', False)])
    # print ("panel_cats %s" % panel_cats)
    # for c in self:
    #     if c.id in [cat.id for cat in panel_cats]:
    #         c.panel_categ_id = c.id
    #     else:
    #         panel_cat = c.parent_id
    #         print ("panel_cat %s" % panel_cat)
    #         while panel_cat.id not in [cat.id for cat in panel_cats]:
    #             panel_cat = panel_cat.parent_id
    #         c.panel_categ_id = panel_cat
    def validate_mold_product(self, product, l):
        invalid_fields = []
        if product.category_code == 'mold':
            sellers = product.seller_ids

            for sl in sellers:
                data_correct = False
                has_material = False  # or not sellers

                if sl.product_material == parse_str(l.material):
                    has_material = True

                if has_material:
                    data_correct = True
                    break
                else:
                    continue
            if not data_correct:
                invalid_fields.append('material')

            lines = {}
            for line in l.atlas_id.atlas_line_ids.filtered(lambda x: parse_str(x.bom_no) == parse_str(l.bom_no) and
                                                                     parse_str(x.name) == parse_str(l.name) and
                                                                     parse_str(x.code) == parse_str(l.code)):
                lines[line.material] = line.name
            if len(lines) > 1:
                invalid_fields.append('name')
                invalid_fields.append('material')

        return invalid_fields

    @api.multi
    def _compute_invalid_fields(self):
        limit_process_num = {}
        process_num_invalid_fields = []
        invalid_line = []
        for l in self:
            mold_product = self.env['product.product'].with_context(lang=None).search(
                [('category_code', '=', 'mold'),
                 ('default_code', '=', parse_str(l.code)),
                 ])
            l.product_id = None
            invalid_fields = l.validate_mold_product(mold_product, l)
            if l.categ_code in ['raw', 'aluminum']:
                if len(parse_str(l.material)) == 0:
                    invalid_fields.append('material')

            key = "%s" % parse_str(l.name)
            if key in limit_process_num and parse_str(l.code) != limit_process_num[key]:
                process_num_invalid_fields.append('name')
                process_num_invalid_fields.append('code')
                invalid_line.append(key)
                # print ("invalid_line %s" % invalid_line)
            else:
                limit_process_num[key] = parse_str(l.code)
            l.invalid_fields = json.dumps(invalid_fields)

        if len(invalid_line) != 0:
            f = l.atlas_id.atlas_line_ids.filtered(lambda x: parse_str(x.name) in [k for k in invalid_line])
            for i in f:
                original_invalid = json.loads(i.invalid_fields)
                for p in process_num_invalid_fields:
                    original_invalid.append(p)
                i.invalid_fields = json.dumps(original_invalid)

            # if parse_str(l.assembly_section) not in ['框架', '框面', '其他', '不控管']:
            #     invalid_fields.append('assembly_section')
            # if len(parse_str(l.code)) > 0:
            # mold_attr = self.env['product.attribute.value'].with_context(lang=None).search(
            #     [('name', '=', parse_str(l.material_no))])
            # mold_product = self.env['product.product'].with_context(lang=None).search(
            #     [('category_code', '=', 'mold'), ('default_code', '=', parse_str(l.code))])
            # if not mold_product:
            #     invalid_fields.append('code')

            # if len(parse_str(l.cutting_length)) > 0:
            #     try:
            #         float(l.cutting_length)
            #     except ValueError:
            #         invalid_fields.append('cutting_length')
            # if len(parse_str(l.cutting_width)) > 0:
            #     try:
            #         float(l.cutting_width)
            #     except ValueError:
            #         invalid_fields.append('cutting_width')
            # if len(parse_str(l.unit_qty)) > 0:
            #     try:
            #         float(l.unit_qty)
            #     except ValueError:
            #         invalid_fields.append('unit_qty')
            # if len(parse_str(l.qty)) > 0:
            #     try:
            #         float(l.qty)
            #     except ValueError:
            #         invalid_fields.append('qty')
        #     invalid_fields = []
        #     invalid_fields = l.validate_product(mold_product, l)
        #     if len(invalid_fields) == 0:
        #         attr = self.env['product.attribute.value'].sudo().with_context({'lang': 'en_US'}).search(
        #             [('name', '=', l.order_length.strip())])
        #         product = self.env['product.product'].search(
        #             [('categ_id', '=', l.demand_id.categ_id.id), ('default_code', '=', l.name.strip()),
        #              ('attribute_value_ids', '=', attr.id)])
        #         invalid_fields = l.validate_product(product, l)
        #         if len(invalid_fields) == 0:
        #             l.product_id = product
        #
        #     l.invalid_fields = json.dumps(invalid_fields)

    # @api.multi
    # # @api.depends('name', 'bom_no', 'material_no')
    # def _compute_production_id(self):
    #     cats = self.env['product.category'].search([('code', '!=', False)])
    #     assembly_cat = self.env['product.category'].search([('code', '=', 'assembly')], limit=1)
    #     others_cat = self.env['product.category'].search([('code', '!=', 'others')], limit=1)
    #     for p in self.sudo():
    #         if not p.name or p.name == "":
    #             continue
    #         cat = others_cat
    #         for c in cats:
    #             if any(key in p.description for key in [k.name for k in c.keywords]):
    #                 cat = c
    #                 break
    #         bom = self.env['mrp.bom'].sudo().search([('product_id.name', '=', p.bom_no)], limit=1)
    #         if not bom:
    #             bom_product = self.env['product.product'].sudo().search([('name', '=', p.bom_no), ('categ_id', '=', assembly_cat.id)], limit=1)
    #             if not bom_product:
    #                 bom_product = self.env['product.product'].sudo().create({
    #                     'categ_id': assembly_cat.id,
    #                     'name': p.bom_no,
    #                     'type': 'product',
    #                     'material': p.material_no,
    #                     'cutting_length': p.cutting_length
    #                 })
    #             bom = self.env['mrp.bom'].sudo().create({
    #                     'product_tmpl_id': bom_product.product_tmpl_id.id,
    #                     'product_id': bom_product.id,
    #                     # 'product_id': bom_product.id,
    #                     # 'product_qty': p.qty
    #                 })
    #         product = self.env['product.product'].sudo().search([('name', '=', p.name)], limit=1)
    #         if not product:
    #             product = self.env['product.product'].sudo().create({
    #                 'categ_id': cat.id,
    #                 'name': p.name,
    #                 'type': 'product',
    #                 # 'material': p.material_no,
    #                 # 'cutting_length': p.cutting_length
    #             })
    #             # product.create_variant_ids()
    #
    #         bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.name == p.name)
    #         if not bom_line:
    #             bom_line = self.env['mrp.bom.line'].sudo().create({
    #                 'product_id': product.id,
    #                 'product_qty': parse_float(p.unit_qty),
    #                 'bom_id': bom.id
    #             })
    #         bom_line.product_qty = parse_float(p.unit_qty)
    #
    #         production_id = self.env['mrp.production'].sudo().search([('contract_id', '=', p.atlas_id.contract_id.id), ('bom_id', '=', bom.id)])
    #
    #         if not production_id and bom:
    #             production_id = self.env['mrp.production'].sudo().create({
    #                 'contract_id': p.atlas_id.contract_id.id,
    #                 'bom_id': bom.id,
    #                 'product_id': bom.product_id.id,
    #                 'product_uom_id': bom.product_id.uom_id.id,
    #                 'product_qty': parse_float(p.qty)
    #             })
    #             p.production_id = production_id

# have_bom.append(bom_product.name)


# bom = self.env['mrp.bom'].sudo().search(
#     [('project_id', '=', project_id.id),
#      ('product_id.default_code', '=', p.bom_no),
#      ('atlas_id', '=', p.atlas_id.edit_atlas_id.id)], limit=1)
# if not bom:
#     product = self.env['product.product'].sudo().search(
#         [('project_id', '=', project_id.id),
#          ('default_code', '=', p.name)], limit=1)
#     if not product:
#         bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == p.name)
#         if not bom_line:
#             bom_product = self.env['product.product'].sudo().search(
#                 [('name', '=', p.bom_no),
#                  ('project_id', '=', project_id.id),
#                  ('categ_id', '=', p.categ_id.id)], limit=1)
#             if not bom_product:
#                 bom_product = self.env['product.product'].sudo().create({
#                     'project_id': project_id.id,
#                     'categ_id': p.categ_id.id,
#                     'name': p.bom_no,
#                     'default_code': p.bom_no,
#                     'type': 'product',
#                     # 'material': p.material_no
#                 })
#             bom = self.env['mrp.bom'].sudo().create({
#                 'project_id': project_id.id,
#                 'product_tmpl_id': bom_product.product_tmpl_id.id,
#                 'product_id': bom_product.id,
#                 # 'product_qty': p.qty
#             })

# no name, no unit_qty is BOM number, not atlas_line.
# if (not al.name or len(al.name.strip()) == 0) and (not al.unit_qty or len(al.unit_qty.strip()) == 0):
#     boms[bom.id] = [bom, parse_float(al.qty)]


#     product = self.env['product.product'].sudo().search(
#         [('project_id', '=', project_id.id), ('default_code', '=', p.name)], limit=1)
#     if not product:
#         product = self.env['product.product'].sudo().create({
#             'project_id': project_id.id,
#             'categ_id': p.categ_id.id,
#             'name': parse_str(p.description),
#             'default_code': parse_str(p.name),
#             'type': 'product',
#             # 'size': parse_str(p.cutting_length),
#             'cutting_length': parse_float(p.cutting_length),
#             'cutting_width': parse_float(p.cutting_width),
#             'volume': parse_float(p.cutting_length) if p.categ_id.code == 'refine' else 0,
#             # 'material': parse_str(p.material_no),
#             'coating': parse_str(p.coating),
#             'color_code': parse_str(p.color_code),
#             'heating': parse_str(p.heating)
#         })

#
#     if p.categ_id.code == 'refine':
#         r_bom = self.env['mrp.bom'].sudo().search([('product_id.default_code', '=', p.name)], limit=1)
#         if not r_bom:
#             r_bom = self.env['mrp.bom'].sudo().create({
#                 'product_tmpl_id': product.product_tmpl_id.id,
#                 'product_id': product.id
#             })
#         boms[r_bom.id] = [r_bom, parse_float(p.qty)]
#         r_bom_line = bom.bom_line_ids.filtered(
#             lambda l: l.product_id.default_code == p.material_no.strip())

# m_products = self.env['product.product'].sudo().search(
#     [('default_code', '=', parse_str(p.material_no)), ('volume', '>', 0)])
# min_rest = 0
# l_product = None
# l_qty = 0
# for v in m_products:
#     print "%s / %s" % (product.volume, v.volume)
#     rest = (v.volume - 200) % product.volume
#     if min_rest == 0 or min_rest > rest:
#         min_rest = rest
#         l_product = v
#         l_qty = product.volume / (v.volume - 200 - rest)
#
# if l_product and not r_bom_line:
#     r_bom_line = self.env['mrp.bom.line'].sudo().create({
#         'product_id': l_product.id,
#         'product_qty': l_qty,
#         'bom_id': r_bom.id
#     })
