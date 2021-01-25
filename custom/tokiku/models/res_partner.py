# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"
    _rec_name = "street"

    is_company = fields.Boolean(string='Is a Company', default=True,
        help="Check if the contact is a company, otherwise it is a person")
    project_ids = fields.Many2many('project.project', string='Projects')
    phone_ext = fields.Char(string='Phone Ext')
    prod_catg_ids = fields.Many2many('product.category', string='Product Category')
    invoice_address = fields.Char(string='Invoice Address')
    customer_info_ids = fields.One2many('tokiku.customer_info', 'customer_id', compute='_compute_customer' ,string='Customer Info')
    supplier_info_ids = fields.One2many('tokiku.supplier_info', 'supplier_id', string='Supplier Info')


    # main_contact_ids = fields.One2many('res.partner', string='Main Contacts', compute='_compute_main_contact_ids')
    # compute = '_compute_supplier',
    # main_contact = fields.Many2one('res.partner', string='Main Contact')
    # main_contact_phone = fields.Char(related='main_contact.phone')
    # main_contact_email = fields.Char(related='main_contact.email')
    # main_contact_mobile = fields.Char(related='main_contact.mobile')
    # main_contact_ext = fields.Char(related='main_contact.phone_ext')

    @api.onchange('name')
    def onchange_name(self):
        if self.name and len(self.name) > 4:
            self.ref = self.name[:4]
        else:
            self.ref = self.name


    _sql_constraints = [
        ('ref_uniq', 'unique(ref)', "Short name already exists!"),
        ('vat_uniq', 'unique(vat)', "Tax Identification Number already exists!"),
        ('name_uniq', 'unique(name)', "Company Name already exists!"),
    ]

    @api.multi
    def _compute_customer(self):
        for ctmr in self:
            customer = ctmr.env['tokiku.customer_info'].search([
                ('customer_id.id', '=', ctmr.id),
            ])
            ctmr.customer_info_ids = customer
        # print self.customer_info_ids
        # compute_customer_ids = self.customer_info_ids.filtered(lambda x: x.customer_id.id == self.id)
        # print compute_customer_ids
        # self.customer_info_ids = compute_customer_ids

    # @api.multi
    # def _compute_main_contact_ids(self):
    #     for c in self:
    #         customer = c.env['tokiku.customer_info'].search([('customer_id.id', '=', c.id )])
    #         c.main_contact_ids = customer.main_contact_ids


    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name')
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, show_function=None, show_street=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)


    @api.multi
    def name_get(self):
        res = []
        for partner in self:
            # name = partner.ref or partner.name or ''
            name = partner.name or ''

            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)

            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')

            if self._context.get('show_function')and partner.function:
                name = "%s/%s" % (name, partner.function)

            if self._context.get('show_street')and partner.street:
                name = "%s/%s" % (name, partner._display_address(without_company=True))

            if self._context.get('show_delivery_address')and partner.type == 'delivery':
                if partner.street:
                    name = "%s/%s" % (name, partner.street)
            res.append((partner.id, name))
        return res
        # res = super(ResPartner, self).name_get()

    # def create_stock_location(self, vals, name=None):
    #     _logger.info('ResPartner create: %s' % vals)
    #     location_name = name
    #     if not name:
    #         location_name = '%d' % vals['message_follower_ids'][0][2]['res_id']
    #
    #     prod_catg_ids = vals['prod_catg_ids'][0][2]
    #     if prod_catg_ids and len(prod_catg_ids) > 0:
    #         for pcid in prod_catg_ids:
    #             pc = self.env['product.category'].search([('id', '=', pcid)])
    #             # if pc.parent_id and (pc.parent_id.name == u'加工' or pc.parent_id.name == u'Processing'):
    #             if pc.parent_id.id == self.env.ref('tokiku.product_category_processing').id:
    #                 _logger.info('pc name: %s,%s' % (pc.parent_id.name, pc.name))
    #                 slref_id = None
    #                 sl = None
    #
    #                 if pc.id == self.env.ref('tokiku.product_category_cut_aluminum').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_cut_plate').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_cut_iron').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_cut_steel').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_cut_stone').id:
    #                     slref_id = self.env.ref('tokiku.stock_location_cut').id
    #                 elif pc.id == self.env.ref('tokiku.product_category_paint_plate').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_paint_steel').id or pc.id == self.env.ref(
    #                         'tokiku.product_category_paint_iron').id:
    #                     slref_id = self.env.ref('tokiku.stock_location_paint').id
    #                 elif pc.id == self.env.ref('tokiku.product_category_heat').id:
    #                     slref_id = self.env.ref('tokiku.stock_location_heat').id
    #                 elif pc.id == self.env.ref('tokiku.product_category_assembly').id:
    #                     slref_id = self.env.ref('tokiku.stock_location_assembly').id
    #                 else:
    #                     pass

                    # if pc.name == u'不鏽鋼烤漆' or pc.name == 'Paint Steel' or pc.name == u'鋁板烤漆' or pc.name == 'Paint Plate' or pc.name == u'鐵件烤漆' or pc.name == 'Paint Iron':
                    #     slref_id = self.env.ref('tokiku.stock_location_paint').id
                    # elif (pc.name == u'熱處理' or pc.name == 'Heat Treatment'):
                    #     slref_id = self.env.ref('tokiku.stock_location_heat').id
                    # elif pc.name == u'石材裁切' or pc.name == 'Cut Stone' or pc.name == u'不鏽鋼裁切' or pc.name == 'Cut Steel' or pc.name == u'鐵件裁切' or pc.name == 'Cut Iron' or pc.name == u'鋁板裁切' or pc.name == 'Cut Plate' or pc.name == u'鋁擠型裁切' or pc.name == 'Cut Aluminum' or pc.name == u'鋁擠型加工' or pc.name == 'Aluminum Refine':
                    #     slref_id = self.env.ref('tokiku.stock_location_cut').id
                    # elif (pc.name == u'組裝' or pc.name == 'Assembly'):
                    #     slref_id = self.env.ref('tokiku.stock_location_assembly').id
                    # else:
                    #     pass

                    # if slref_id:
                    #     sl = self.env['stock.location'].search(
                    #         [('name', '=', location_name), ('location_id', '=', slref_id)])
                    #
                    # if slref_id and not sl:
                    #     _logger.info('stock.location does not exist: %s ' % sl)
                    #     crt_info = {
                    #         'name': location_name,
                    #         'location_id': slref_id,
                    #         'usage': 'internal'
                    #     }
                    #     _logger.info('crt_info: %s' % crt_info)
                    #     sup_loc_id = self.env['stock.location'].create(crt_info)
                    #     if sup_loc_id:
                    #         sl = self.env['stock.location'].search(
                    #             [('name', '=', location_name), ('location_id', '=', slref_id)])
                    #         pending_info = {
                    #             'name': '待處理',
                    #             'location_id': sl.id,
                    #             'usage': 'internal'
                    #         }
                    #         _logger.info('crt_info: %s' % pending_info)
                    #         self.env['stock.location'].create(pending_info)
                    #         done_info = {
                    #             'name': '完工',
                    #             'location_id': sl.id,
                    #             'usage': 'internal'
                    #         }
                    #         _logger.info('crt_info: %s' % done_info)
                    #         self.env['stock.location'].create(done_info)
                    # else:
                    #     _logger.info('stock.location exist: %s ' % sl)

    # @api.model
    # def create(self, vals):
    #     result = super(ResPartner, self).create(vals)
    #     if vals.get('prod_catg_ids', False):
    #         self.create_stock_location(vals)
    #     return result
    #
    # @api.multi
    # def write(self, vals):
    #     result = super(ResPartner, self).write(vals)
    #     _logger.info('ResPartner write: %s' % vals)
    #     if vals.get('prod_catg_ids', False):
    #         location_name = '%d' % self.id
    #         self.create_stock_location(vals, location_name)
    #     return result


    # def _compute_project_history(self):
    #     prj_list = []
    #     print(self.name)
    #     search_projects = self.env['project.project'].search([('partner_id', '=', self.id),('project_ids')])
    #
    #     for prj in search_projects:
    #         prj_list.append(prj.id)
    #     return {'domain': {'project_history_ids': [('id', 'in', prj_list)]}}
# common fields
# is_default = fields.Boolean(string='Default Contact', default=True)
# fullName = fields.Char(string='Full Name')
# shortName = fields.Char(string='Short Name')
# owner = fields.Char(string='Owner')
# companyTel = fields.Char(string='Company Tel')
# companyAddr = fields.Char(string='Company Addr')
# companyFax = fields.Char(string='Company Fax')
# companyMail = fields.Char(string='Company Mail')
# firstContact = fields.Char(string='First Contact')
# phoneExt = fields.Char(string='Phone Extension')
# contactJobTitle = fields.Char(string='Job Title')
# contactDept = fields.Char(string='Dept')
#
# # customer fields
# customerNum = fields.Char(string='Customer Num', copy=False, readonly=True, index=True, default=lambda self: _('New'))
# project_ids = fields.One2many('project.project', 'partner_id', string='Projects')
#
# # supplier fields
# supplierNum = fields.Char(string='Supplier Num', copy=False, readonly=True, index=True, default=lambda self: _('New'))
# isActive = fields.Boolean(string='Is Active', default=True)
# bankName = fields.Char(string='Bank')
# bankAccount = fields.Char(string='Bank Account')
# accountName = fields.Char(string='Account Name')
# invoiceAddr = fields.Char(string='invoice Addr')
# payMethod = fields.Many2one('tokiku.pay_method', string='Pay Method')
# payment = fields.Many2one('tokiku.payment', string='Payment')
# bizItems = fields.One2many('tokiku.business_item', 'supplier_id', string='Business Items')
# factory_ids = fields.One2many('tokiku.factory', 'supplier_id', string='Business Items')
#
#
# @api.model
# def create(self, vals):
# 	_logger.info('create vals: %s' % vals)
#
# 	if vals.get('supplier') is True:
# 		tmp_seq = self.env['ir.sequence'].next_by_code('tokiku.supplier') or _('New')
# 		vals['name'] = vals.get('fullName')
# 		vals['supplierNum'] = tmp_seq
# 	elif vals.get('customer') is True:
# 		tmp_seq = self.env['ir.sequence'].next_by_code('tokiku.customer') or _('New')
# 		vals['name'] = vals.get('fullName') or vals.get('name')
# 		vals['customerNum'] = tmp_seq
#
# 	if vals.get('shortName'):
# 		vals['shortName'] = vals['name'][:2]
#
# 	result = super(ResPartner, self).create(vals)
# 	return result


