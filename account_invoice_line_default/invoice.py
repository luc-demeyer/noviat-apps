# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2011 Noviat nv/sa (www.noviat.be). All rights reserved.
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

from osv import fields, osv
from tools.translate import _
from lxml import etree
import netsvc
logger=netsvc.Logger()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(account_invoice, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if not context.get('account_invoice_line_default', False):
            if view_type == 'form':
                view_obj = etree.XML(res['arch'])
                find = etree.XPath("/form/notebook/page/field[@name='invoice_line']")
                invoice_line = find(view_obj)
                extra_ctx = "'account_invoice_line_default': 1, 'inv_name': name, 'inv_type': type, 'inv_partner_id': partner_id"
                for el in invoice_line:
                    ctx = el.get('context')      
                    #ctx = el.get('default_get')      
                    if ctx:
                        ctx_strip = ctx.rstrip("}").strip().rstrip(",")    
                        ctx = ctx_strip + ", " + extra_ctx + "}"
                    else:
                        ctx = "{" + extra_ctx + "}"
                    el.set('context', str(ctx))
                    #el.set('default_get', str(ctx))
                    res['arch'] = etree.tostring(view_obj)
                """ 
                 code infra adds support for account_invoice_layout module
                """
                view_obj = etree.XML(res['arch'])
                find = etree.XPath("/form/notebook/page/field[@name='abstract_line_ids']")
                invoice_line = find(view_obj)
                extra_ctx = "'account_invoice_line_default': 1, 'inv_name': name, 'inv_type': type, 'inv_partner_id': partner_id"
                for el in invoice_line:
                    ctx = el.get('context')      
                    #ctx = el.get('default_get')      
                    if ctx:
                        ctx_strip = ctx.rstrip("}").strip().rstrip(",")    
                        ctx = ctx_strip + ", " + extra_ctx + "}"
                    else:
                        ctx = "{" + extra_ctx + "}"
                    el.set('context', str(ctx))
                    #el.set('default_get', str(ctx))
                    res['arch'] = etree.tostring(view_obj)
        #logger.notifyChannel('addons.'+self._name, netsvc.LOG_WARNING, 'arch = %s' % res['arch'])
        return res

account_invoice()
    
class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def _inv_name_default(self, cr, uid, context=None):
        name = None
        if context is None:
            context = {}
        if context and context.has_key('inv_name'):
            name = context['inv_name']
        return name
    
    def _inv_account_default(self, cr, uid, context=None):
        partner_obj = self.pool.get('res.partner')
        account_id = None
        inv_type = None
        if context is None:
            context = {}
        if context and context.has_key('inv_type'):
            if context.get('inv_partner_id'):
                partner = self.pool.get('res.partner').browse(cr, uid, context['inv_partner_id'], context=context)
                if context['inv_type'] in ['in_invoice', 'in_refund']:
                    account_id = partner.property_in_inv_acc and partner.property_in_inv_acc.id or False
                if context['inv_type'] in ['out_invoice', 'out_refund']:
                    account_id = partner.property_out_inv_acc.id and partner.property_out_inv_acc.id or False
        return account_id

    def _inv_tax_default(self, cr, uid, context=None):
        partner_obj = self.pool.get('res.partner')
        account_obj = self.pool.get('account.account')
        fpos_obj = self.pool.get('account.fiscal.position')
        account_id = None
        inv_type = None
        res = []
        if context is None:
            context = {}
        if context and context.has_key('inv_type'):
            if context.get('inv_partner_id'):
                partner = self.pool.get('res.partner').browse(cr, uid, context['inv_partner_id'], context=context)
                if context['inv_type'] in ['in_invoice', 'in_refund']:
                    account_id = partner.property_in_inv_acc.id
                if context['inv_type'] in ['out_invoice', 'out_refund']:
                    account_id = partner.property_out_inv_acc.id
                if account_id:
                    taxes = account_obj.browse(cr, uid, account_id).tax_ids
                    fposition_id = partner.property_account_position
                    fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id) or False
                    res = fpos_obj.map_tax(cr, uid, fpos, taxes)
        return res
    
    _defaults = {
        'name': _inv_name_default,
        'account_id': _inv_account_default,
        'invoice_line_tax_id': _inv_tax_default,
    }
account_invoice_line()
