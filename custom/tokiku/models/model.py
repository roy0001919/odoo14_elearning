# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
import json
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TokikuPayMethod(models.Model):
    _name = 'tokiku.pay_method'

    payMethod = fields.Char(string='Pay Method')

    @api.multi
    @api.depends('payMethod')
    def name_get(self):
        result = []
        for i in self:
            name = i.payMethod
            result.append((i.id, name))
        return result


class TokikuPayment(models.Model):
    _name = 'tokiku.payment'

    payment = fields.Char(string='Payment')

    @api.multi
    @api.depends('payment')
    def name_get(self):
        result = []
        for i in self:
            name = i.payment
            result.append((i.id, name))
        return result


class TokikuTxCategory(models.Model):
    _name = 'tokiku.tx_category'

    txCategory = fields.Char(string='Tx Category')

    @api.multi
    @api.depends('txCategory')
    def name_get(self):
        result = []
        for i in self:
            name = i.txCategory
            result.append((i.id, name))
        return result


class TokikuFactory(models.Model):
    _name = 'tokiku.factory'

    name = fields.Char(string='Factory Name')
    addr = fields.Char(string='Factory Address')
    fax = fields.Char(string='Factory Fax')
    tel = fields.Char(string='Factory Tel')

    supplier_id = fields.Many2one('res.partner', string='supplier')


class DrawingReply(models.Model):
    _name = 'tokiku.drawing_reply'

    name = fields.Char('Reply Content')


class OrderCategory(models.Model):
    _name = 'tokiku.order_category'

    name = fields.Char('Order Category')
    code = fields.Char('Code')

    _sql_constraints = [
        ('code', 'unique(code)', 'The code of the order category must be unique!'),
    ]


class SupplierInfo(models.Model):
    _name = 'tokiku.supplier_info'

    _sql_constraints = [
        ('supplier_info_uniq', 'unique(supplier_id, prod_catg)',
         _('The supplier_id and prod_catg for the supplier_info must be unique!')),
    ]

    name = fields.Char(related='supplier_id.name', store=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    prod_catg = fields.Many2one('product.category', string='Product Category')
    # prod_catg = fields.Many2many('product.category', string='Product Category')
    project_id = fields.Many2one('project.project')
    main_contact_ids = fields.Many2many('res.partner', string='Main Contacts')
    tx_category = fields.Many2one('tokiku.tx_category', string='Transaction Category')
    payment = fields.Many2one('tokiku.payment', string='Payment')
    pay_method = fields.Many2one('tokiku.pay_method', string='Pay Method')

    project_name = fields.Char(string='Project Name', related='project_id.name')
    project_code = fields.Char(string='Project Code', related='project_id.project_code')


    @api.model
    def create(self, vals):
        # SupplierInfo create: {u'prod_catg': [[6, False, [8, 5]]], u'supplier_ids': 11}
        si = super(SupplierInfo, self).create(vals)
        # _logger.info('SupplierInfo create: %s' % vals)
        # prod_catg_ids = vals['prod_catg'][0][2]
        # sup_id = vals['supplier_id']
        # print sup_id
        # sup = self.env['res.partner'].search([('id', '=', sup_id.id)])
        # for pcid in prod_catg_ids:
        #     pc = self.env['product.category'].search([('id', '=', pcid)])
        #
        #     # _logger.info('pc name: %s,%s' % (pc.parent_id.name, pc.name))
        #     if pc.parent_id and (pc.parent_id.name == u'加工' or pc.parent_id.name == u'Processing'):
        #         _logger.info('pc name: %s,%s' % (pc.parent_id.name, pc.name))
        #         slref_id = None
        #         sl = None
        #
        #         if pc.name == u'不鏽鋼烤漆' or pc.name == 'Paint Steel':
        #             slref_id = self.env.ref('tokiku.stock_location_paint').id
        #         elif (pc.name == u'鋁板烤漆' or pc.name == 'Paint Plate'):
        #             slref_id = self.env.ref('tokiku.stock_location_paint').id
        #         elif (pc.name == u'鐵件烤漆' or pc.name == 'Paint Iron'):
        #             slref_id = self.env.ref('tokiku.stock_location_paint').id
        #         elif (pc.name == u'熱處理' or pc.name == 'Heat Treatment'):
        #             slref_id = self.env.ref('tokiku.stock_location_heat').id
        #         elif (pc.name == u'石材裁切' or pc.name == 'Cut Stone'):
        #             slref_id = self.env.ref('tokiku.stock_location_cut').id
        #         elif (pc.name == u'不鏽鋼裁切' or pc.name == 'Cut Steel'):
        #             slref_id = self.env.ref('tokiku.stock_location_cut').id
        #         elif (pc.name == u'鐵件裁切' or pc.name == 'Cut Iron'):
        #             slref_id = self.env.ref('tokiku.stock_location_cut').id
        #         elif (pc.name == u'鋁板裁切' or pc.name == 'Cut Plate'):
        #             slref_id = self.env.ref('tokiku.stock_location_cut').id
        #         elif (pc.name == u'鋁擠型裁切' or pc.name == 'Cut Aluminum'):
        #             slref_id = self.env.ref('tokiku.stock_location_cut').id
        #         elif (pc.name == u'組裝' or pc.name == 'Assembly'):
        #             slref_id = self.env.ref('tokiku.stock_location_assembly').id
        #         elif (pc.name == u'鋁擠型加工' or pc.name == 'Aluminum Refine'):
        #             pass
        #         else:
        #             pass
        #
        #         if slref_id:
        #             sl = self.env['stock.location'].search([('name', '=', sup.name), ('location_id', '=', slref_id)])
        #             # sl = self.env['stock.location'].search([('name', '=', sup.name), ('location_id', '=', slref_id), ('project_id', '=', si.project_id.id)])
        #
        #         if slref_id and not sl:
        #             _logger.info('stock.location does not exist: %s ' % sl)
        #             crt_info = {
        #                 'name': sup.name,
        #                 'location_id': slref_id,
        #                 'usage': 'internal',
        #                 'partner_id': vals['supplier_id'],
        #                 'project_id': si.project_id.id,
        #             }
        #             _logger.info('crt_info: %s' % crt_info)
        #             self.env['stock.location'].create(crt_info)
        #         else:
        #             _logger.info('stock.location exist: %s ' % sl)

        return si


class CustomerInfo(models.Model):
    _name = 'tokiku.customer_info'

    name = fields.Char(string='Name', related='customer_id.name', store=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    project_id = fields.Many2one('project.project')
    main_contact_ids = fields.Many2many('res.partner', string='Main Contacts')
    system_type = fields.Char(string='System Type')

    project_name = fields.Char(related='project_id.name', string='Project Name')
    project_code = fields.Char(related='project_id.project_code', string='Project Code')


class MainContacts(models.Model):
    _name = 'tokiku.main_contact'


    @api.multi
    @api.depends('project_id.customer_info_ids')
    def _compute_external_partner_domain(self):
        for object in self:
            partner_list = []
            contact_list = []
            if object.project_id.customer_info_ids:
                print("if")
                custs = object.project_id.customer_info_ids
                partner_list = [x.customer_id for x in custs]

                for partner in partner_list:
                    contacts = partner.child_ids
                    for c in contacts:
                        contact_list.append(c.id)

                object.external_partner_domain = json.dumps(
                [('id', 'in', contact_list)]
            )
            else:
                raise ValidationError(" 客戶標籤欄位請先填入資料，才能將資料帶進此欄位 ")
            # if object.project_id.customer_info_ids:
            #     custs = object.project_id.customer_info_ids
            #     partner_list = [x.customer_id for x in custs]
            #
            #     for partner in partner_list:
            #         contacts = partner.child_ids
            #         for c in contacts:
            #             contact_list.append(c.id)
            #
            #     object.external_partner_domain = json.dumps(
            #     [('id', 'in', contact_list)]
            # )


    external_partner_domain = fields.Char(compute="_compute_external_partner_domain", readonly=True, store=False)
    customer_id = fields.Many2one(related='main_contact_id.parent_id', string='Customer', readonly=True)
    main_contact_id = fields.Many2one('res.partner', string='Main Contacts')
    function = fields.Char(related='main_contact_id.function', string='Job Position')
    work_place = fields.Char(string='Work Place')
    phone = fields.Char(related='main_contact_id.phone', string='Phone')
    mobile = fields.Char(related='main_contact_id.mobile', string='Mobile')

    project_id = fields.Many2one('project.project')
    # project_customer_list = fields.One2many(related='project_id.customer_info_ids')
    # project_customer_list = fields.Many2one('res.partner', compute='_get_project_customer_id', store=True)


    # @api.onchange('customer_id')
    # def _onchange_customer_id(self):
    #     # for object in self:
    #     # self.ensure_one()
    #     customer_list = []
    #     for cus in self.project_id.customer_info_ids:
    #         customer_list.append(cus)
    #     print(customer_list)
    #     return {'domain': {'customer_id': [('id', 'in', customer_list)]}}

    # @api.multi
    # @api.depends('project_id.customer_info_ids')
    # def _compute_external_partner_domain(self):
    #     for object in self:
    #         partner_list = []
    #         if object.project_id.customer_info_ids:
    #             custs = object.project_id.customer_info_ids
    #             partner_list = [x.customer_id.id for x in custs]
    #
    #         object.external_partner_domain = json.dumps(
    #             [('id', 'in', partner_list)]
    #         )



class RelatedCompany(models.Model):
    _name = 'tokiku.related_company'

    name = fields.Char(string='Name')
    related_department = fields.Selection([
        ('owner consultant', 'Owner Consultant'),
        ('architect', 'Architect'),
        ('architect consultant', 'Architect Consultant'),
        ('construction plant', 'Construction Plant'),
        ('construction plant consultant', 'Construction Plant Consultant'),
        ('supervision unit', 'Supervision Unit'),
        ('construction management', 'Construction Management')],
        string='Related Department', default="owner consultant")


    company_name = fields.Char(string='Company Name')
    main_contact = fields.Char(string='Main Contact')
    phone = fields.Char(string='Phone')
    phone_ext = fields.Char(string='Phone Ext')
    mobile = fields.Char(string='Mobile')

    project_id = fields.Many2one('project.project', string='Project')



class MoldCombination(models.Model):
    _name = 'tokiku.mold_combinaiton'

    name = fields.Char('Mold Combination')


class OrderUnit(models.Model):
    _name = 'tokiku.order_unit'

    name = fields.Char('Order Unit')


class PaymentUnit(models.Model):
    _name = 'tokiku.payment_unit'

    name = fields.Char('Payment Unit')


class PricingUnit(models.Model):
    _name = 'tokiku.pricing_unit'

    name = fields.Char('Pricing Unit')


class DemandUnit(models.Model):
    _name = 'tokiku.demand_unit'

    name = fields.Char('Demand Unit')


class AssemblingInstallationPrice(models.Model):
    _name = 'tokiku.assembling_installation_price'

    name = fields.Integer(string='Assembling Installation Price')


class UserCustomizedPriceUnit(models.Model):
    _name = 'tokiku.user_customized_price_unit'

    name = fields.Char(string='User Customized Price Unit')


class ConstructionSection(models.Model):
    _name = 'tokiku.construction_section'

    name = fields.Char(string='Construction Section')


class ExaminingResult(models.Model):
    _name = 'tokiku.examining_result'

    name = fields.Char(string='Examining Result')


class InstallationCategory(models.Model):
    _name = 'tokiku.installation_category'

    name = fields.Char('Installation Category')


class InstallLocation(models.Model):
    _name = 'tokiku.install_location'

    name = fields.Char('Install Location')