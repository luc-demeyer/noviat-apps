# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import logging
_logger = logging.getLogger(__name__)


class billing_period(orm.Model):
    _name = 'billing.period'
    _description = 'Periods for recurring billing'
    _order = 'code'

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'code': fields.char('Code', size=12, required=True),
        'base_period': fields.selection([
            ('day','Day'),
            ('week','Week'),
            ('month','Month'),
            ('year','Year'),
            ], 'Billing Base Period', required=True),  
        'base_period_multiplier': fields.integer('Base Period Multiplier', required=True,
            help="Multiplier on base period for recurring billing."),
        'company_id': fields.many2one('res.company', 'Company'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'base_period_multiplier': 1,
        'company_id': lambda s, cr, uid, ctx: s.pool.get('res.company')._company_default_get(cr, uid, 'account.account', context=ctx),
        'active': True,
    }    
    _sql_constraints = [
        ('code', 'unique (code)', 'The code must be unique !')
    ]

    def _check_multiplier(self, cr, uid, ids, context=None):
        return self.browse(cr, uid, ids[0]).base_period_multiplier > 0 and True or False

    _constraints = [
        (_check_multiplier, 'Error! The Base Period Multiplier must be > 0 !', ['base_period_multiplier'])
    ]


class product_category(orm.Model):
    _inherit = 'product.category'
    _columns = {
        # sale
        'billing_type_sale': fields.selection([
            ('recurring','Recurring Charge'),
            ('one_time','One Time Charge'),
            ], 'Billing Type - Sale'),  
        'billing_result_sale': fields.selection([
            ('open','Open Invoice'),
            ('draft','Draft Invoice'),
            ('manual','Manual Invoice'),
            ], 'Invoicing Action',
            help="This parameter determines how an invoice is created from the billing data."
                 "\n'Draft' prevails in case of multiple lines with different Invoice States."),
        'billing_period_sale_id': fields.many2one('billing.period', 'Billing Periodicity',
            help="Billing Periodicity for recurring Sales Contracts"),
        'billing_unlimited_sale': fields.boolean('Unlimited',
            help="Check this box for recurring billing with no determined end date."),
        'billing_period_nbr_sale': fields.integer('Number of Periods',
            help="Default Number of Billing Periods for recurring Sales Contracts"),
        # purchase
        'billing_type_purchase': fields.selection([
            ('recurring','Recurring Charge'),
            ('one_time','One Time Charge'),
            ], 'Billing Type - Purchase'),  
        'billing_period_purchase_id': fields.many2one('billing.period', 'Billing Periodicity',
            help="Billing Periodicity for recurring Purchases Contracts"),
        'billing_unlimited_purchase': fields.boolean('Unlimited',
            help="Check this box for recurring billing with no determined end date."),
        'billing_period_nbr_purchase': fields.integer('Number of Periods',
            help="Default Number of Billing Periods for recurring Purchases Contracts"),
    }


class product_template(orm.Model):
    _inherit = 'product.template'
    _columns = {
        # sale
        'billing_type_sale': fields.selection([
                ('recurring','Recurring Charge'),
                ('one_time','One Time Charge'),
                ], 'Billing Type - Sale'),  
        'billing_result_sale': fields.selection([
            ('open','Open Invoice'),
            ('draft','Draft Invoice'),
            ('manual','Manual Invoice'),
            ], 'Invoicing Action',
            help="This parameter determines how an invoice is created from the billing data."
                 "\n'Draft' prevails in case of multiple lines with different Invoice States."),
        'billing_period_sale_id': fields.many2one('billing.period', 'Billing Periodicity',
            help="Billing Periodicity for recurring Sales Contracts"),
        'billing_unlimited_sale': fields.boolean('Unlimited',
            help="Check this box for recurring billing with no determined end date."),
        'billing_period_nbr_sale': fields.integer('Number of Periods',
            help="Default Number of Billing Periods for recurring Sales Contracts"),
        # purchase
        'billing_type_purchase': fields.selection([
                ('recurring','Recurring Charge'),
                ('one_time','One Time Charge'),
                ], 'Billing Type - Purchase'),  
        'billing_period_purchase_id': fields.many2one('billing.period', 'Billing Periodicity',
            help="Billing Periodicity for recurring Purchases Contracts"),
        'billing_unlimited_purchase': fields.boolean('Unlimited',
            help="Check this box for recurring billing with no determined end date."),
        'billing_period_nbr_purchase': fields.integer('Number of Periods',
            help="Default Number of Billing Periods for recurring Purchases Contracts"),
    }
    _defaults = {
        'billing_unlimited_sale': True,
        'billing_unlimited_purchase': True,
    }

