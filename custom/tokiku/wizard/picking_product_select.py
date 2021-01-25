from odoo import api, fields, models, _
import logging
from odoo.exceptions import Warning as UserWarning
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PickingProdInfo(models.TransientModel):
    _name = 'tokiku.picking_product_info'
    _description = 'Picking Product Info'

    product_id = fields.Many2one('product.product', string='Product')
    default_code = fields.Char(related='product_id.default_code', store=True)
    tokiku_default_code = fields.Char(string="Tokiku Default Code")
    qty_done = fields.Float('Done')
    atlas_id = fields.Many2one('tokiku.atlas', string='Atlas')
    atlas_short_name = fields.Char('Short Name', related='atlas_id.short_name')


class PickingProductSelect(models.TransientModel):
    _name = 'tokiku.picking_product_select'
    _description = 'Picking Product Select'

    tmp_grid = fields.Many2many('tokiku.picking_product_info', string='Grid')
    partner_id = fields.Many2one('res.partner', string='Supplier')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        get_supplier_id = self.env.context.get('default_supplier_id')
        self.partner_id = get_supplier_id

        wizard_lines = []
        picking_id = self.env.context.get('picking_id')
        stock_picking_id = self.env['stock.picking'].sudo().browse(picking_id)

        # if len(stock_picking_id.pack_operation_product_ids) == 0 and not stock_picking_id.picking_type_entire_packs:
        for ml in stock_picking_id.move_lines:
            if len(stock_picking_id.atlas_ids) == 0 or ml.atlas_id.id in [s.id for s in stock_picking_id.atlas_ids]:
                wizard_lines.append((0, 0, {'product_id': ml.product_id.id,
                                            # 'tokiku_default_code': prod.product_id.mold_id.default_code,
                                            'tokiku_default_code': ml.panel_line_id.mold_id.default_code,
                                            'atlas_id': ml.atlas_id,
                                            'qty_done': ml.product_uom_qty,
                                            }))

        # else:
        #     for prod in stock_picking_id.pack_operation_product_ids:
        #         wizard_lines.append((0, 0, {'product_id': prod.product_id.id,
        #                                     'tokiku_default_code': prod.product_id.mold_id.default_code,
        #                                     'qty_done': prod.product_qty,
        #                                 }))
        self.tmp_grid = wizard_lines

    @api.multi
    def back_picking(self):
        picking_id = self.env.context.get('picking_id')
        stock_picking_id = self.env['stock.picking'].browse(picking_id)
        select_prod_id = []
        select_picking_id = []

        for rec in self.tmp_grid:
            if rec.tokiku_default_code:
                select_prod_id.append([rec.default_code, rec.atlas_id.id, rec.tokiku_default_code])
            else:
                select_picking_id.append([rec.default_code, rec.atlas_id.id])
        if len(stock_picking_id.pack_operation_product_ids) == 0 and not stock_picking_id.picking_type_entire_packs:
            for rec in self.tmp_grid:
                for prod in stock_picking_id.move_lines:
                    if [prod.default_code, prod.atlas_id.id, prod.code] not in select_prod_id and rec.tokiku_default_code:
                        prod.unlink()
                    elif [prod.default_code, prod.atlas_id.id] not in select_picking_id and rec.tokiku_default_code == False:
                        prod.unlink()
                for prod in stock_picking_id.move_lines:
                    if rec.product_id.id == prod.product_id.id:
                        prod.product_uom_qty = rec.qty_done
                        if rec.qty_done <= prod.product_uom_qty:
                            pass
                        else:
                            raise UserError(_('The quantity received is more than the order quantity.'))

        elif len(stock_picking_id.pack_operation_product_ids) > 0 and stock_picking_id.state != 'done':
            for rec in self.tmp_grid:
                for prod in stock_picking_id.pack_operation_product_ids:
                    if [prod.default_code, prod.atlas_id.id,
                        prod.code] not in select_prod_id and rec.tokiku_default_code:
                        prod.unlink()
                    elif [prod.default_code,
                          prod.atlas_id.id] not in select_picking_id and rec.tokiku_default_code == False:
                        prod.unlink()
                for prod in stock_picking_id.pack_operation_product_ids:
                    if rec.product_id.id == prod.product_id.id:
                        if rec.qty_done <= prod.product_qty:
                            prod.qty_done = rec.qty_done
                        else:
                            raise UserWarning(_('The quantity received is more than the order quantity.'))

        return {'type': 'ir.actions.act_window_close'}
