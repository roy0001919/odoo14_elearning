# -*- coding: utf-8 -*-

import logging

from core.biznavi.utils import parse_float, parse_str, parse_int
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class NewVersionAtlas(models.TransientModel):
    _name = 'tokiku.version_wizard'
    _description = 'New Version Atlas'

    new_version_atlas_reason = fields.Char(string='New Version Atlas Reason', require=True)
    design_change_atlas_version = fields.Char(string='Design Change Atlas Version')

    # new_atlas_version = fields.Integer('New Atlas Version')
    # default=lambda self: self._get_design_change_ver(),)
    # last_design_change_ver = fields.Char(compute='_compute_design_change_ver')

    @api.multi
    def act_confirm(self):

        atlas_id = self.env.context.get('atlas_id')
        atlas = self.env['tokiku.atlas'].browse(atlas_id)

        if not atlas.is_imported and atlas.atlas_version == 0:
            atlas.is_imported = True
            atlas.edit_atlas_id = atlas

        edit_atlas = atlas.edit_atlas_id
        new_atlas = edit_atlas.copy()

        reason = self.new_version_atlas_reason
        new_atlas.new_version_atlas_reason = reason
        edit_atlas.new_version_atlas_reason = reason
        new_atlas.is_imported = True
        last_atlas = self.env['tokiku.atlas'].search([('edit_atlas_id', '=', atlas.edit_atlas_id.id)],
                                                     order="atlas_version desc", limit=1)
        new_atlas.atlas_version = last_atlas.atlas_version + 1
        new_atlas.design_change_atlas_version = self.design_change_atlas_version
        edit_atlas.design_change_atlas_version = self.design_change_atlas_version

        project_id = self.env.user.project_id
        # products = []
        id_map = {}
        count = 0
        # for p in new_atlas.atlas_line_ids:
        #     count = count+1
        #     print ("count %d" % count)
        #     if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #         continue
        #
        #     # if category code
        #     if p.categ_id.code == 'aluminum' or 'raw':
        #         product = self.env['product.product'].sudo().search(
        #             [('project_id', '=', project_id.id),
        #              ('categ_id', '=', p.categ_id.id),
        #              ('default_code', '=', p.name),
        #              ('part_no', '=', p.code),
        #              ], limit=1)
        #         # print ("aluminum")
        #     else:
        #         product = self.env['product.product'].sudo().search(
        #             [('project_id', '=', project_id.id),
        #              ('categ_id', '=', p.categ_id.id),
        #              ('default_code', '=', p.name),
        #              ], limit=1)
        #
        #     if not product:
        #         product = self.env['product.product'].sudo().create({
        #             'project_id': project_id.id,
        #             'categ_id': p.categ_id.id,
        #             'default_code': parse_str(p.name),
        #             'part_no': parse_str(p.code),
        #             'name': parse_str(p.description),
        #             'type': 'product',
        #         })
        #     id_map[p.id] = product.id
        al_dict = {}
        for al in atlas.atlas_line_ids:
            if al.panel_categ_id.code:
                al_key = "%s/%s" % (al.panel_categ_id.code, al.name)
                if al_dict.get(al.panel_categ_id.code):
                    if al_dict[al.panel_categ_id.code].get(al_key):
                        al_dict[al.panel_categ_id.code][al_key] = [al, al_dict[al.panel_categ_id.code][al_key][
                            1] + parse_int(al.qty)]
                    else:
                        al_dict[al.panel_categ_id.code][al_key] = [al, parse_int(al.qty)]
                else:
                    al_dict[al.panel_categ_id.code] = {}
                    al_dict[al.panel_categ_id.code][al_key] = [al, parse_int(al.qty)]

        _logger.info('al_dict:%s' % al_dict)

        # pl_dict = {}
        line_count = 0
        for code in al_dict.iterkeys():
            _logger.info('code:%s' % code)
            categ = self.env['product.category'].sudo().search([('code', '=', code),
                                                                ('parent_id.code', '!=', 'assembly_section')])
            panel = self.env['tokiku.panel'].sudo().search(
                [('project_id', '=', self.env.user.project_id.id),
                 ('categ_id', '=', categ.id)], limit=1)
            if not panel:
                panel = self.env['tokiku.panel'].sudo().create(
                    {'project_id': self.env.user.project_id.id,
                     'categ_id': categ.id})

            pl_dict = {}
            #  use edit atlas id to identify the newest atlas information, ex: name changed
            for pl in panel.line_ids.filtered(lambda x: x.atlas_id.id == atlas.edit_atlas_id.id):
                pl.atlas_demand_qty = 0
                pl_key = "%s/%s" % (code, pl.default_code)
                _logger.info('pl pkey:%s' % pl_key)

                if not pl_dict.get(pl_key):
                    pl_dict[pl_key] = [pl]
                # Clear all this atlas items in panel line to 0 to avoid items are deleted and qty isn't clear

            _logger.info('pl_dict:%s' % pl_dict)
            line_insert = []
            count = 0
            # for al in atlas.atlas_line_ids.filtered(lambda x: x.panel_categ_id.id == categ.id and x.name):
            # qty_dict = {}
            for key in al_dict.get(code).iterkeys():
                al = al_dict[code][key][0]
                al_qty = al_dict[code][key][1]
                count = count + 1
                line_count += 1
                # if al.panel_categ_id.code == 'raw':
                # elif al.panel_categ_id.code == 'aluminum':
                # else:
                # pls = panel.line_ids.filtered(lambda x: x.default_code == al.name and x.atlas_id.id == atlas.edit_atlas_id.id)
                # x.code == al.code)

                p_key = "%s/%s" % (code, al.name)
                _logger.info('al pkey:%s' % p_key)
                if pl_dict.get(p_key):
                    # pl.atlas_demand_qty = 0

                    for pl in pl_dict[p_key]:
                        pl.atlas_id = atlas.edit_atlas_id
                        pl.atlas_demand_qty += al_qty
                        pl.description = parse_str(al.description)
                        pl.surface_coating = parse_str(al.coating)
                        pl.color_code = parse_str(al.color_code)
                        pl.assembly_section = parse_str(al.assembly_section)
                        pl.material = parse_str(al.material)
                        pl.assembly_section = parse_str(al.assembly_section)
                else:
                    if code in ['aluminum', 'raw']:
                        product = self.env['product.product'].sudo().search(
                            [('project_id', '=', project_id.id),
                             ('categ_id', '=', al.categ_id.id),
                             ('default_code', '=', al.name),
                             ('part_no', '=', al.code),
                             ], limit=1)
                        product._compute_mold_id()

                    else:
                        product = self.env['product.product'].sudo().search(
                            [('project_id', '=', project_id.id),
                             ('categ_id', '=', al.categ_id.id),
                             ('default_code', '=', al.name),
                             ], limit=1)
                    if not product:
                        product = self.env['product.product'].sudo().create({
                            'project_id': project_id.id,
                            'categ_id': al.categ_id.id,
                            'default_code': parse_str(al.name),
                            'part_no': parse_str(al.code),
                            'name': parse_str(al.description),
                            'type': 'product',
                        })
                    # print ('prod_categ_id %s' % al.panel_categ_id.id)
                    line_insert.append((0, 0, {'product_id': product.id,
                                               'atlas_id': atlas.edit_atlas_id.id,
                                               # use edit_atlas_id to keep atlas data up to date
                                               'atlas_demand_qty': al_qty,
                                               'atlas_bom': parse_str(al.bom_no),
                                               'description': parse_str(al.description),
                                               'code': parse_str(al.code),
                                               'cutting_length': parse_float(al.cutting_length),
                                               'cutting_width': parse_float(al.cutting_width),
                                               'color_code': parse_str(al.color_code),
                                               'heating': parse_str(al.heating),
                                               'surface_coating': parse_str(al.coating),
                                               'atlas_unit_qty': parse_float(al.unit_qty),
                                               'material': parse_str(al.material),
                                               'assembly_section': parse_str(al.assembly_section),
                                               'prod_categ_id': al.panel_categ_id, }))
            panel.sudo().line_ids = line_insert

            # panel._compute_order_line_ids()
            # panel.line_ids._compute_order_lines()
            panel.line_ids._compute_demand_qty()
            panel.line_ids._compute_rest_demand_qty()
            panel.line_ids._compute_area()
            # panel.refresh = True

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
        # return {'type': 'ir.actions.act_window_close'}

        # if pd.category_code == code:
        #     for pd in products:
        #         panel.line_ids
        #
        #         pl_exist_prod = self.env['tokiku.panel_line'].sudo().search(
        #             [('atlas_id', '=', new_atlas.id), ('default_code', '=', pd.default_code)], limit=1)
        #         print pl_exist_prod
        #
        #         if pl_exist_prod and pd.category_code == code:
        #             # for p in new_atlas.atlas_line_ids:
        #             #     for pl in panel.line_ids:
        #             #         if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #             #             continue
        #             #         if p.name == pl.default_code:
        #             #             pl.demand_qty = p.qty
        #
        #         if not pl_exist_prod and pd.category_code == code:
        #             _logger.info("=======================================")
        #             panel.sudo().line_ids = [(0, 0, {'product_id': pd.id, 'atlas_id': new_atlas.id})]

        # for p in new_atlas.atlas_line_ids:
        #     for pl in panel.line_ids:
        #         if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #             continue
        #         if p.name == pl.default_code:
        #             pl.demand_qty = p.qty

        # product = self.env['product.product'].sudo().search(
        #     [('project_id', '=', project_id.id), ('default_code', '=', p.name)], limit=1)
        # exist_prod = self.env['tokiku.panel_line'].sudo().search(
        #     [('atlas_id', '=', new_atlas.id), ('default_code', '=', pd.default_code)])
        # print exist_prod
        #
        # if exist_prod and pd.category_code == code:
        #     _logger.info("000000")
        #
        #     for p in new_atlas.atlas_line_ids.filtered(lambda x: x.project_id.id == pd.project_id and x.name == pd.default_code):
        #         if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #             _logger.info("000555")
        #             continue
        #
        #         _logger.info("111111")
        #         exist_prod.demand_qty = p.qty
        #
        # if (not exist_prod) and pd.category_code == code:
        #     _logger.info("222222")

        # self.order_line.filtered(lambda l: l.linked_line_id.id == line.id)

        # for pd in products:
        #
        #     _logger.info("=======================================")
        #     exist_prod = self.env['tokiku.panel_line'].sudo().search(
        #         [('atlas_id', '=', new_atlas.id), ('default_code', '=', pd.default_code)])
        #     print exist_prod
        #
        #     if exist_prod and pd.category_code == code:
        #         _logger.info("000000")
        #
        #         for p in new_atlas.atlas_line_ids.filtered(lambda x: x.name == pd.default_code):
        #             if (not p.name or len(p.name.strip()) == 0) and (
        #                 not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #                 _logger.info("000555")
        #                 continue
        #
        #             _logger.info("111111")
        #             exist_prod.demand_qty = p.qty
        #
        #     if (not exist_prod) and pd.category_code == code:
        #         _logger.info("222222")
        #         panel.sudo().line_ids = [(0, 0, {'product_id': pd.id, 'atlas_id': new_atlas.id})]

        # for p in new_atlas.atlas_line_ids:
        #     for pl in panel.line_ids:
        #         if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
        #             continue
        #         if p.name == pl.default_code:
        #             pl.demand_qty = p.qty
        # panel.compute_line_ids()
        # new_atlas.is_imported = True

        # form_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_atlas_form')[1]
        # return {
        #     'name': _('Atlas'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'tokiku.atlas',
        #     'view_id': form_id,
        #     'type': 'ir.actions.act_window',
        #     'target': 'current',
        #     'res_id': new_atlas.id
        # }
# project_id = new_atlas.env.user.project_id
#         for a in new_atlas:
#             boms = {}
#             for p in a.atlas_line_ids:
#                 if not p.bom_no or len(p.bom_no.strip()) == 0:
#                     continue
#                 bom = new_atlas.env['mrp.bom'].sudo().search(
#                     [('project_id', '=', project_id.id), ('product_id.default_code', '=', p.bom_no)], limit=1)
#                 if not bom:
#                     bom_product = new_atlas.env['product.product'].sudo().search(
#                         [('name', '=', p.bom_no), ('project_id', '=', project_id.id), ('categ_id', '=', p.categ_id.id)],
#                         limit=1)
#                     if not bom_product:
#                         bom_product = new_atlas.env['product.product'].sudo().create({
#                             'project_id': project_id.id,
#                             'categ_id': p.categ_id.id,
#                             'name': p.bom_no,
#                             'default_code': p.bom_no,
#                             'type': 'product',
#                             # 'material': p.material_no
#                         })
#                     bom = new_atlas.env['mrp.bom'].sudo().create({
#                         'project_id': project_id.id,
#                         'product_tmpl_id': bom_product.product_tmpl_id.id,
#                         'product_id': bom_product.id,
#                         # 'product_qty': p.qty
#                     })
#                 if (not p.name or len(p.name.strip()) == 0) and (not p.unit_qty or len(p.unit_qty.strip()) == 0):
#                     boms[bom.id] = [bom, parse_float(p.qty)]
#                 else:
#                     product = new_atlas.env['product.product'].sudo().search(
#                         [('project_id', '=', project_id.id), ('default_code', '=', p.name)], limit=1)
#                     if not product:
#                         product = new_atlas.env['product.product'].sudo().create({
#                             'project_id': project_id.id,
#                             'categ_id': p.categ_id.id,
#                             'name': parse_str(p.description),
#                             'default_code': parse_str(p.name),
#                             'type': 'product',
#                             # 'size': parse_str(p.cutting_length),
#                             'cutting_length': parse_float(p.cutting_length),
#                             'cutting_width': parse_float(p.cutting_width),
#                             'volume': parse_float(p.cutting_length) if p.categ_id.code == 'refine' else 0,
#                             # 'material': parse_str(p.material_no),
#                             'coating': parse_str(p.coating),
#                             'color_code': parse_str(p.color_code),
#                             'heating': parse_str(p.heating)
#                         })
#                     bom_line = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == p.name)
#                     if not bom_line:
#                         bom_line = new_atlas.env['mrp.bom.line'].sudo().create({
#                             'product_id': product.id,
#                             'product_qty': parse_float(p.unit_qty),
#                             'bom_id': bom.id
#                         })
#                     bom_line.product_qty = parse_float(p.unit_qty)
#
#
#             for code in ['refine', 'glass', 'plate', 'steel', 'iron', 'stone', 'accessories', 'others']:
#                 categ = new_atlas.env['product.category'].sudo().search([('code', '=', code)])
#                 panel = new_atlas.env['tokiku.panel'].sudo().search(
#                     [('contract_id', '=', a.contract_id.id), ('categ_id', '=', categ.id)])
#                 if not panel:
#                     panel = new_atlas.env['tokiku.panel'].sudo().create(
#                         {'contract_id': a.contract_id.id, 'categ_id': categ.id})
#                 for p in a.production_ids.filtered(lambda x: x.product_id.categ_id.code == 'assembly'):
#                     for bl in p.bom_id.bom_line_ids.filtered(lambda x: x.product_id.categ_id.code == code):
#                         pl = panel.line_ids.filtered(lambda x: x.product_id.id == bl.product_id.id)
#                         if not pl:
#                             panel.sudo().line_ids = [(0, 0, {'product_id': bl.product_id.id})]
#
#                 panel.compute_line_ids()
#                 a.is_imported = True

# for p in a.production_ids.filtered(lambda x: x.product_id.categ_id.code == 'assembly'):
#     for bl in p.bom_id.bom_line_ids.filtered(lambda x: x.product_id.categ_id.code == code):
#         pl = panel.line_ids.filtered(lambda x: x.product_id.id == bl.product_id.id)
#         if not pl:
