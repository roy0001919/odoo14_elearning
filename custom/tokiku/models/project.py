# -*- coding: utf-8 -*-
import logging
import re

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    # @api.multi
    # @api.depends('contract_ids.maintenance_ticket_delivery_date')
    # def compute_date_warranty_start(self):
    #     for rec in self:
    #         rec.date_warranty_start = rec.contract_ids[0].maintenance_ticket_delivery_date

    project_code = fields.Char(string='Project Code')
    short_name = fields.Char(string='Project Short Name')
    owner_advisor = fields.Char(string='Owner Advisor')
    architect = fields.Char(string='Architect')
    architect_advisor = fields.Char(string='Architect Advisor')
    construction_company = fields.Char(string='Construction Company')
    construction_advisor = fields.Char(string='Construction Advisor')
    supervision = fields.Char(string='Supervision Unit')
    total_area = fields.Float(string='Total Area')
    # c
    system_developer = fields.Char(string='System Developer')
    site_address = fields.Char(string='Site Address')
    site_phone = fields.Char(string='Site Phone')
    site_mobile = fields.Char(string='Site Mobile')
    site_contact = fields.Char(string='Site Contact')
    date_contract = fields.Date(string='Contract Date')
    date_warranty_start = fields.Date(string='Warranty Start Date')
    # default = compute_date_warranty_start
    date_warranty_end = fields.Date(string='Warranty End Date')
    scheduled_complete_date = fields.Date(string='Scheduled Complete Date')
    actual_complete_date = fields.Date(string='Actual Complete Date')
    project_start_date = fields.Date(string='Project Start Date')

    settle_day = fields.Integer(string='Settle Day')
    payment_day = fields.Integer(string='Payment Day')
    remark = fields.Text(string='Remark')
    warranty_warning = fields.Boolean(compute='_compute_date')
    system_type = fields.Char(string='System Type', compute='_compute_system_type')

    # supplier_ids = fields.Many2many('res.partner', string='Suppliers')
    mold_ids = fields.One2many('tokiku.mold', 'project_id', string='Molds')
    contract_ids = fields.One2many('account.analytic.contract', 'project_id', string='Contracts')
    contract_id = fields.Many2one('account.analytic.contract', string='Contract')
    building_ids = fields.One2many('tokiku.building', 'project_id', string='Building')
    order_ids = fields.One2many('purchase.order', 'project_id', string='Order Forms')
    sale_order_ids = fields.One2many('sale.order', 'project_id', string='Sale Order Forms')
    const_atlas_ids = fields.One2many('tokiku.const_atlas', 'project_id', string='Construction Atlas')
    # picking_wave_ids = fields.One2many('stock.picking.wave', 'project_id', string='Picking Waves')
    picking_ids = fields.One2many('stock.picking', 'project_id', string='Pickings')

    customer_info_ids = fields.One2many('tokiku.customer_info', 'project_id', string='Customers')
    show_first_customer = fields.Char(compute='_compute_first_customer_name')
    supplier_info_ids = fields.One2many('tokiku.supplier_info', 'project_id', string='Suppliers')
    related_company_ids = fields.One2many('tokiku.related_company', 'project_id', string='Related Company')

    main_contact_ids = fields.One2many('tokiku.main_contact', 'project_id', string='Supplier Main Contacts')
    # 'tokiku.customer_info', 'main_contact_ids',
    # _compute_main_contact_ids
    has_contract_maintenance_ticket_date = fields.Boolean(default=True)
    # compute = '_has_contract_maintenance_ticket_date',
    panel_ids = fields.One2many('tokiku.panel', 'project_id', string='Panels')
    estimate_ids = fields.One2many('tokiku.estimate_amount', 'project_id', string='Estimate Amount')

    state = fields.Selection([
        ('draft', 'Plan'),
        ('construction', 'Construction'),
        ('done', 'Completed'),
        ('warranty', 'Warranty'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=False, copy=False, index=True, track_visibility='onchange', default='draft')

    _sql_constraints = [
        ('code_project_uniq', 'unique(project_code)', 'The code of the project must be unique!'),
        ('short_name_uniq', 'unique(short_name)', 'The short name must be unique!'),
    ]

    # @api.model_cr_context
    # def _auto_init(self):
    #     self._sql_constraints = [
    #         ('code_project_uniq', 'unique(project_code)', 'The code of the project must be unique!')
    #     ]
    #     super(Project, self)._auto_init()

    # @api.multi
    # @api.one
    # def _compute_main_contact_ids(self):
    #     main_contact_list = []
    #
    #     for c in self.customer_info_ids:
    # customer = c.env['tokiku.customer_info'].search([('project_id.id', '=', c.id)])
    # for cust in customer:
    #     main_contact_list.append(c.main_contact_ids)
    # self.main_contact_ids = main_contact_list
    def open_not_purchase_table(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_not_purchase_table')[1]

        return {
            'name': _('Panel Not Purchase Table'),
            # 'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'tokiku.panel_line',
            # 'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'domain': [('panel_id.project_id', '=', self.env.user.project_id.id),
                       ('rest_demand_qty', '>', 0),
                       ('panel_id.categ_code', 'not in', ['mold', 'raw'])
                       ],
            # 'context': {'default_line_ids': not_purchase_table}
        }

    # def open_panel_summary(self):
    #     view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_summary')[1]
    #
    #     return {
    #         'name': _('Panel Summary'),
    #         # 'view_type': 'form',
    #         'view_mode': 'tree',
    #         'res_model': 'tokiku.panel_line',
    #         # 'res_id': self.id,
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id,
    #         'target': 'current',
    #         'flags': {'form': {'action_buttons': True}},
    #         'domain': [],
    # }

    def open_order_line_summary(self):
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_order_line_summary')[1]

        return {
            'name': _('Order Line Summary'),
            # 'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchase.order.line',
            # 'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'domain': [('project_id', '=', self.env.user.project_id.id),
                       ],
    }

    # def _create_stock_location(self, sup_info_ids):
    #     for sup_info_id in sup_info_ids:
    #         if sup_info_id[0] == 0:
    #
    #             pcid = sup_info_id[2].get('prod_catg')
    #             sup_id = sup_info_id[2].get('supplier_id')
    #
    #             sup = self.env['res.partner'].search([('id', '=', sup_id)])
    #             pc = self.env['product.category'].search([('id', '=', pcid)])
    #
    #             if sup and pc:
    #                 if pc.parent_id and (pc.parent_id.name == u'加工' or pc.parent_id.name == u'Processing'):
    #                     slref_id = None
    #                     sl = None
    #
    #                     if pc.name == u'不鏽鋼烤漆' or pc.name == 'Paint Steel' or pc.name == u'鋁板烤漆' or pc.name == 'Paint Plate' or pc.name == u'鐵件烤漆' or pc.name == 'Paint Iron':
    #                         slref_id = self.env.ref('tokiku.stock_location_paint').id
    #                     elif (pc.name == u'熱處理' or pc.name == 'Heat Treatment'):
    #                         slref_id = self.env.ref('tokiku.stock_location_heat').id
    #                     elif (pc.name == u'組裝' or pc.name == 'Assembly'):
    #                         slref_id = self.env.ref('tokiku.stock_location_assembly').id
    #                     elif (pc.name == u'鋁擠型加工' or pc.name == 'Aluminum Refine'):
    #                         slref_id = self.env.ref('tokiku.stock_location_refine').id
    #                     else:
    #                         pass
    #
    #                     if slref_id:
    #                         sl = self.env['stock.location'].search([('name', '=', sup.name), ('location_id', '=', slref_id)])
    #
    #                     if not sl:
    #                         crt_info = {
    #                                 'name': sup.name,
    #                                 'location_id': slref_id,
    #                                 'usage': 'internal',
    #                                 'partner_id': sup_id,
    #                             }
    #                         sup_crt = self.env['stock.location'].create(crt_info)
    #
    #                         #  last layer of stock location
    #                         crt_info['location_id'] = sup_crt.id
    #                         crt_info['name'] = u'Pending'
    #                         self.env['stock.location'].create(crt_info)
    #                         crt_info['name'] = u'Done'
    #                         self.env['stock.location'].create(crt_info)

    @api.model
    def create(self, vals):
        self.clear_caches()
        project = super(Project, self).create(vals)
        if not self.env.user.project_id:
            self.env.user.project_id = project

        return project

    @api.multi
    def write(self, vals):
        self.ensure_one()
        # warranty_start = vals.get('date_warranty_start')
        # original_warranty_start = self.date_warranty_start

        # if 'state' in vals:
        if vals.get('state') == 'done':
            if not self.actual_complete_date and not vals.get('actual_complete_date'):
                raise ValidationError(_("Actual Complete Date is required"))
        if vals.get('state') == 'warranty':
            if not self.date_warranty_start and not vals.get('date_warranty_start'):
                raise ValidationError(_("Date Warranty Start is required"))
        if vals.get('state') == 'expired':
            if len(self.contract_ids) == 0 or not self.contract_ids[0].maintenance_ticket_retrieval_date:
                raise ValidationError(_("Maintenance Ticket Retrieval Date is required"))

        # sup_info_ids = vals.get('supplier_info_ids')
        # if sup_info_ids:
        #     self._create_stock_location(sup_info_ids)
        return super(Project, self).write(vals)

    @api.constrains('project_code')
    def validate_project_code(self):
        for rec in self:
            if re.match("^[A-Za-z0-9\-]+$", rec.project_code) == None:
                raise ValidationError("Only numbers, letters and minus are allowed: %s" % rec.project_code)

            return True

    @api.multi
    def act_set(self, values):
        self.clear_caches()
        self.env.user.project_id = self.id
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def open_mold(self):
        # code = 'mold'
        # category_name = 'Mold'
        view_id = self.env['ir.model.data'].get_object_reference('tokiku', 'view_panel_mold_form')[1]
        # categ = self.env['product.category'].search([('code', '=', code)])
        # if not categ:
        #     categ = self.env['product.category'].create({'name': category_name, 'code': code})
        mold_categ = self.env['product.category'].sudo().search([('code', '=', 'mold')])
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        panel = self.env['tokiku.panel'].sudo().search(
            [('project_id', '=', self.env.user.project_id.id), ('categ_id', '=', mold_categ.id)], limit=1)

        # panel.refresh = True
        # if panel.refresh:
        #     panel.calculate()
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create(
                {'project_id': self.env.user.project_id.id, 'categ_id': mold_categ.id})

        return {
            'name': _('Mold'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.panel',
            'res_id': panel.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_project_id': self.id, 'default_categ_id': mold_categ.id}
        }

    @api.one
    @api.depends('date_warranty_end')
    def _compute_date(self):
        today = fields.Datetime.now()

        if self.state != 'expired':
            if self.date_warranty_end and today:
                today_dt = fields.Datetime.from_string(today)
                warranty_end_dt = fields.Datetime.from_string(self.date_warranty_end)
                difference = relativedelta(warranty_end_dt, today_dt)
                days = difference.days
                hours = difference.hours
                minutes = difference.minutes
                seconds = 0

                if days < 15:
                    self.warranty_warning = True
        else:
            self.warranty_warning = False

    # @api.one
    # @api.depends('customer_info_ids', 'system_type')
    # def _compute_system_type(self):
    #     for customer_info in self.customer_info_ids:
    #         if self.partner_id.id == customer_info.customer_id.id:
    #             self.system_type = customer_info.system_type
    #         else:
    #             continue

    @api.multi
    def _compute_system_type(self):
        for rec in self:
            for c in rec.customer_info_ids:
                rec.system_type = c.system_type
                break

    @api.multi
    def _compute_first_customer_name(self):
        for rec in self:
            for c in rec.customer_info_ids:
                rec.show_first_customer = c.name
                break

    # @api.multi
    # def _has_contract_maintenance_ticket_date(self):
    #     for rec in self:
    #         con = self.env['account.analytic.contract'].search([('project_id', '=', rec.id)])
    #         if len(con) > 0:
    #             ticket_delivery_date = con[0].maintenance_ticket_delivery_date
    #             if ticket_delivery_date:
    #                 rec.has_contract_maintenance_ticket_date = True
    #             else:
    #                 rec.has_contract_maintenance_ticket_date = False

    @api.onchange('contract_ids')  # if these fields are changed, call method
    def _onchange_contract_ids(self):
        # print(self.contract_ids)

        if len(self.contract_ids) > 0:
            if self.contract_ids[0].maintenance_ticket_delivery_date:
                self.has_contract_maintenance_ticket_date = True
                if not self.date_warranty_start:
                    self.date_warranty_start = self.contract_ids[0].maintenance_ticket_delivery_date
                    # print(self.contract_ids[0].maintenance_ticket_delivery_date)
            if not self.contract_ids[0].maintenance_ticket_delivery_date:
                self.has_contract_maintenance_ticket_date = False

        if len(self.contract_ids) == 0:
            self.has_contract_maintenance_ticket_date = False
        else:
            pass

    # @api.onchange('state')  # if these fields are changed, call method
    # def _onchange_contract_ids(self):

    @api.onchange('name')  # if these fields are changed, call method
    def _onchange_name(self):
        if self.name and len(self.name) > 4:
            self.short_name = self.name[:4]
        else:
            self.short_name = self.name

    @api.multi
    def open_raw_dashboard(self):
        return self.open_dashboard('raw', 'Aluminum Raw Material')

    @api.multi
    def open_refine_dashboard(self):
        return self.open_dashboard('aluminum', 'Aluminum Refine')

    @api.multi
    def open_glass_dashboard(self):
        return self.open_dashboard('glass', 'Glass')

    @api.multi
    def open_plate_dashboard(self):
        return self.open_dashboard('plate', 'Aluminum Plate')

    @api.multi
    def open_steel_dashboard(self):
        return self.open_dashboard('steel', 'Stainless Steel')

    @api.multi
    def open_iron_dashboard(self):
        return self.open_dashboard('iron', 'Iron Pieces')

    @api.multi
    def open_stone_dashboard(self):
        return self.open_dashboard('stone', 'Stone')

    @api.multi
    def open_silicon_dashboard(self):
        return self.open_dashboard('silicon', 'Silicon')

    @api.multi
    def open_rubber_dashboard(self):
        return self.open_dashboard('rubber', 'Rubber')

    @api.multi
    def open_mineral_dashboard(self):
        return self.open_dashboard('mineral', 'Mineral')

    @api.multi
    def open_accessories_dashboard(self):
        return self.open_dashboard('accessories', 'Accessories')

    @api.multi
    def open_others_dashboard(self):
        return self.open_dashboard('others', 'Others')

    @api.multi
    def open_assembly_dashboard(self):
        return self.open_dashboard('assembly', 'Assembly')

    @api.multi
    def open_installation_dashboard(self):
        return self.open_dashboard('installation', 'Installation')

    def open_dashboard(self, code, category_name):
        if not self.env.user.project_id:
            raise UserError(_('Please select a project first!'))
            return

        # form_id = 'view_refine_dashboard'
        # if code in ['glass', 'plate', 'steel', 'iron', 'stone', 'silicon', 'rubber', 'mineral', 'accessories', 'others',
        #             'assembly']:
        form_id = 'view_%s_dashboard' % code

        view_id = self.env['ir.model.data'].get_object_reference('tokiku', form_id)[1]
        categ = self.env['product.category'].sudo().search([('code', '=', code)])
        if not categ:
            categ = self.env['product.category'].sudo().create({'name': category_name, 'code': code})
        panel = self.env['tokiku.panel'].sudo().search([('project_id', '=', self.env.user.project_id.id),
                                                        ('categ_id', '=', categ.id)])

        # if panel.refresh:
        #     panel.calculate()
        if not panel:
            panel = self.env['tokiku.panel'].sudo().create({'project_id': self.env.user.project_id.id,
                                                            'categ_id': categ.id})
        return {
            'name': panel.categ_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tokiku.panel',
            'res_id': panel.id,
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': {'default_categ_id': categ.id,
                        'default_project_id': self.id,
                        'categ_code': categ.code,
                        'panel_type': 'dashboard'}
        }


class Building(models.Model):
    _name = 'tokiku.building'

    name = fields.Char(string='Building Name')
    floor = fields.Integer(string='Floor Number')
    underground = fields.Integer(string='Underground Layers')
    project_id = fields.Many2one('project.project', string='Project')


class ConstructionAtlas(models.Model):
    _name = 'tokiku.const_atlas'

    name = fields.Char(string='Atlas Name')
    version = fields.Char(string='Version')
    date_submission = fields.Date(string='Submission Date')
    submission_number = fields.Char(string='Submission Number')
    date_reply = fields.Date(string='Reply Date')
    reply_number = fields.Char(string='Reply Number')
    # reply_content = fields.Char(string='Reply Content')

    reply_content = fields.Many2one('tokiku.drawing_reply', string='Reply Content')
    drawing_confirm = fields.Boolean('Drawing Confirm')

    note = fields.Text('Note')
    reply_note = fields.Text('Reply Note')

    project_id = fields.Many2one('project.project', string='Project')
    remark = fields.Char('Remark')
    examining_result = fields.Many2one('tokiku.examining_result', string='Examining Result', ondelete='restrict')


class EstimateAmmount(models.Model):
    _name = 'tokiku.estimate_amount'

    project_id = fields.Many2one('project.project')
    product_categ_id = fields.Many2one('product.category', string='Product Category')
    estimate_amount = fields.Float(string='Estimate Amount')
