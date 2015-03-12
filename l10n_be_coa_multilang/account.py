# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _
#import logging
#_logger = logging.getLogger(__name__)

class account_account_type(orm.Model):
    ''' add active flag to hide unused account types from UI '''
    _inherit = 'account.account.type'
    _columns = {
        'active': fields.boolean('Active', select=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    _defaults = {
        'active': 1,
    }

class account_account_template(orm.Model):
    _inherit = 'account.account.template'
    _columns = {
        'name': fields.char('Name', size=256, required=True, select=True, translate=True),
    }

class account_account(orm.Model):
    _inherit = 'account.account'
    
    def _check_account_type(self, cr, uid, ids, context=None):
        """ disable this constraint        
        for account in self.browse(cr, uid, ids, context=context):
            if account.type in ('receivable', 'payable') and account.user_type.close_method != 'unreconciled':
                return False
        """
        return True
    
    _columns = {
        'name': fields.char('Name', size=256, required=True, select=True, translate=True),
    }
    _constraints = [
        # disable this constraint (replace '_check_account_type' method)
        (_check_account_type, 'Configuration Error! \nYou can not select an account type with a deferral method different of "Unreconciled" for accounts with internal type "Payable/Receivable"! ', ['user_type','type']),
    ]
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        """
        method copied from standard account module and modified to add multi-language support on name field
        """
        if context is None: context = {} # Change by Noviat
        if not args:
            args = []
        args = args[:]
        ids = []
        try:
            if name and str(name).startswith('partner:'):
                part_id = int(name.split(':')[1])
                part = self.pool.get('res.partner').browse(cr, user, part_id, context=context)
                args += [('id', 'in', (part.property_account_payable.id, part.property_account_receivable.id))]
                name = False
            if name and str(name).startswith('type:'):
                type = name.split(':')[1]
                args += [('type', '=', type)]
                name = False
        except:
            pass
        if name:
            ids = self.search(cr, user, [('code', '=like', name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('shortcut', '=', name)]+ args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context.get('lang') and {'lang':context['lang']}) # Change by Noviat
            if not ids and len(name.split()) >= 2:
                #Separating code and name of account for searching
                operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

class account_tax_code(orm.Model):
    _inherit = 'account.tax.code'
    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the Tax Case must be unique per company !')
    ]

class account_tax_template(orm.Model):
    _inherit = 'account.tax.template'
    _columns = {
        'name': fields.char('Tax Name', size=64, required=True, translate=True),
    }

class account_tax_code_template(orm.Model):
    _inherit = 'account.tax.code.template'
    _columns = {
        'name': fields.char('Tax Case Name', size=64, required=True, translate=True),
    }

class account_chart_template(orm.Model):
    _inherit = 'account.chart.template'    
    _columns={
        'name': fields.char('Name', size=64, required=True, translate=True),
        'multilang_be':fields.boolean('Multilang Belgian CoA'),
        'bank_from_template':fields.boolean('Banks/Cash from Template', help="Generate Bank/Cash accounts and journals from the Templates."),
    }
    _defaults = {
        'multilang_be': False,
        'bank_from_template': False,
    }    
    _order = 'name'      

class account_fiscal_position_template(orm.Model):
    _inherit = 'account.fiscal.position.template'
    _columns = {
        'name': fields.char('Fiscal Position Template', size=64, required=True, translate=True),      
    }
