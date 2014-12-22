# -*- encoding: utf-8 -*-
# noqa: account_account, name_search is a backport from Odoo.
#       OCA has no control over style here.
#       TODO: make PR to include context sensitive name_search in standard
# flake8: noqa
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

from openerp import models, fields, api, _
from openerp.osv import expression


class account_account_type(models.Model):
    ''' add active flag to hide unused account types from UI '''
    _inherit = 'account.account.type'

    active = fields.Boolean(string='Active', select=True, default=True)
    company_id = fields.Many2one('res.company', string='Company')


class account_account_template(models.Model):
    _inherit = 'account.account.template'

    name = fields.Char(translate=True)


class account_account(models.Model):
    _inherit = 'account.account'

    name = fields.Char(translate=True)

    def _check_account_type(self, cr, uid, ids, context=None):
        """ disable this constraint
        for account in self.browse(cr, uid, ids, context=context):
            if account.type in ('receivable', 'payable') and account.user_type.close_method != 'unreconciled':
                return False
        """
        return True

    _constraints = [
        # the constraint below has been disabled
        (_check_account_type, 'Configuration Error!\nYou cannot select an account type with a deferral method different of "Unreconciled" for accounts with internal type "Payable/Receivable".', ['user_type','type']),
    ]

    def name_search(self, cr, user, name,args=None, operator='ilike', context=None, limit=100):
        """
        method copied from standard account module and modified to add multi-language support on name field
        """
        if context is None:
            context = {}  # Change by Noviat
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
            if operator not in expression.NEGATIVE_TERM_OPERATORS:
                plus_percent = lambda n: n+'%'
                code_op, code_conv = {
                    'ilike': ('=ilike', plus_percent),
                    'like': ('=like', plus_percent),
                }.get(operator, (operator, lambda n: n))

                ids = self.search(cr, user, ['|', ('code', code_op, code_conv(name)), '|', ('shortcut', '=', name), ('name', operator, name)]+args, limit=limit,
                    context=context.get('lang') and {'lang':context['lang']})  # Change by Noviat

                if not ids and len(name.split()) >= 2:
                    #Separating code and name of account for searching
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit,
                        context=context.get('lang') and {'lang':context['lang']})  # Change by Noviat
            else:
                ids = self.search(cr, user, ['&','!', ('code', '=like', name+"%"), ('name', operator, name)]+args, limit=limit,
                    context=context.get('lang') and {'lang':context['lang']})  # Change by Noviat
                # as negation want to restric, do if already have results
                if ids and len(name.split()) >= 2:
                    operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                    ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2), ('id', 'in', ids)]+ args, limit=limit,
                        context=context.get('lang') and {'lang':context['lang']})  # Change by Noviat
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)


class account_tax_code(models.Model):
    _inherit = 'account.tax.code'
    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)',
         'The code of the Tax Case must be unique per company !')
    ]


class account_tax_template(models.Model):
    _inherit = 'account.tax.template'

    name = fields.Char(translate=True)


class account_tax_code_template(models.Model):
    _inherit = 'account.tax.code.template'

    name = fields.Char(translate=True)


class account_chart_template(models.Model):
    _inherit = 'account.chart.template'
    _order = 'name'

    name = fields.Char(translate=True)
    multilang_be = fields.Boolean(string='Multilang Belgian CoA')
    bank_from_template = fields.Boolean(
        string='Banks/Cash from Template',
        help="Generate Bank/Cash accounts and journals from the Templates.")


class account_fiscal_position_template(models.Model):
    _inherit = 'account.fiscal.position.template'

    name = fields.Char(translate=True)
    note = fields.Text(translate=True)


class account_journal(models.Model):
    _inherit = 'account.journal'

    name = fields.Char(translate=True)
