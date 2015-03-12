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
from openerp.tools.translate import _


class contract_invoice_create(orm.TransientModel):
    _name = 'contract.invoice.create'
    _description = 'Create Invoices from Contract Data'

    def _contract_select_default(self, cr, uid, context={}):
        if context.get('active_ids') and len(context['active_ids']) > 1:
            if context.get('default_type') == 'sale':
                return 'all_sale'
            elif context.get('default_type') == 'purchase':
                return 'all_purchase'
        else:
            return 'select'

    def _get_period(self, cr, uid, context={}):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        else:
            return False

    _columns = {
        'contract_select': fields.selection([
            ('all_sale','All Customer Contracts'),
            ('all_purchase','All Supplier Contracts'),
            ('select','Selected Contracts'),
            ],'Contracts', required=True),
        'date_invoice': fields.date('Invoice Date'),
        'period_id': fields.many2one('account.period', 'Period', required=True,
            domain=[('state','=','draft'),('special', '=', False)], 
            help="Select Accounting Period for invoices."),
    }
    _defaults = {
        'contract_select': _contract_select_default,
        'period_id': _get_period,
    }

    def invoice_create(self, cr, uid, ids, context=None, period_id=None):
        contract_obj = self.pool.get('contract.document')
        
        data = ids and self.browse(cr, uid, ids[0], context=context)
        if data:
            date_invoice = data.date_invoice
            period_id = data.period_id.id
            contract_select = data.contract_select
        else:
            if context.get('default_type') == 'sale':
                contract_select = 'all_sale'
            elif context.get('default_type') == 'purchase':
                contract_select = 'all_purchase'
            else:
                raise orm.except_orm(_('Programming Error !'), _('No contract type specified.'))
        if not period_id:            
            raise orm.except_orm(_('Programming Error !'), _('No accounting period specified.'))
        if contract_select == 'select':
            contract_ids = context.get('active_ids') or []
        else:
            contract_ids = contract_obj.search(cr, uid, [('type', '=', contract_select[4:])])
        contract_obj.create_invoice(cr, uid, contract_ids, period_id, date_invoice, context=context)
        return {}
