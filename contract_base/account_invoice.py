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
from openerp.addons.decimal_precision import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _columns = {
        'contract_id': fields.many2one('contract.document', 'Contract Reference'),  
        'print_line_ids': fields.one2many('account.invoice.line.print', 'invoice_id', 
            'Invoice Print Lines', readonly=True, states={'draft':[('readonly',False)]}),
    }

    def unlink(self, cr, uid, ids, context=None):
        clb_obj = self.pool.get('contract.line.billing')
        for inv in self.browse(cr, uid, ids, context): 
            clb_ids = clb_obj.search(cr, uid, [('invoice_id', '=', inv.id)])
            if clb_ids:
                clb_obj.write(cr, uid, clb_ids, {'billed': False})
        return super(account_invoice, self).unlink(cr, uid, ids, context=context)


class account_invoice_line(orm.Model):
    _inherit = 'account.invoice.line'
    _columns = {
        'service_period': fields.char('Service Period', size=23),
    }


class account_invoice_line_print(orm.Model):
    """
    This class allows to add invoice formatting data without impacting the standard OpenERP invoicing process flow.
    """
    _name = 'account.invoice.line.print'
    _order = "invoice_id, sequence asc, id"

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        #_logger.warn('_amount_line, ids=%s, field_name=%s', ids, field_name)
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            subtotal = 0.0
            if line.type == 'normal':
                amt_lines = [line]
            else:
                amt_lines = line.child_ids
            total = 0.0
            total_included = 0.0
            for l in amt_lines:
                price = l.price_unit * (1-(l.discount or 0.0)/100.0)
                taxes = tax_obj.compute_all(cr, uid, l.invoice_line_tax_id, price, l.quantity, product=l.product_id,
                    address_id=l.invoice_id.address_invoice_id, partner=l.invoice_id.partner_id)
                total += taxes['total']
                total_included += taxes['total_included']
            res[line.id] = total
            cur = line.invoice_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice Reference', ondelete='cascade'),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'contract_line_id': fields.many2one('contract.line', 'Contract Line', readonly=True),        
        'name': fields.char('Description', size=256, required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of invoice lines."),
        'type': fields.selection([
            ('heading','Section Heading'),
            ('normal','Normal'),
            ], 'Type', readonly=True),        
        'parent_id': fields.many2one('account.invoice.line.print', 'Section', 
            help="Use this field to order invoice lines in sections whereby the parent_id contains section heading info."),
        'child_ids': fields.one2many('account.invoice.line.print', 'parent_id', 'Section Lines'),
        'hidden': fields.boolean('Hidden',
            help='Use this flag to hide contract lines on the printed Invoice.'),
        'uos_id': fields.related('invoice_line_id', 'uos_id', type='many2one', 
            relation='product.uom', string='Unit of Measure', readonly=True),    
        'product_id': fields.related('invoice_line_id', 'product_id', type='many2one', 
            relation='product.product', string='Product', readonly=True),          
        'price_unit': fields.related('invoice_line_id', 'price_unit', type='float', 
            string='Unit Price', readonly=True, digits_compute=dp.get_precision('Account')),
        'price_subtotal': fields.related('invoice_line_id', 'price_subtotal', type='float', 
            string='Subtotal', digits_compute=dp.get_precision('Account'), readonly=True),      
        'price_subtotal': fields.function(_amount_line, string='Subtotal', type='float',
            digits_compute= dp.get_precision('Account')), 
        'quantity': fields.related('invoice_line_id', 'quantity', type='float', 
            string='Quantity', readonly=True),
        'discount': fields.related('invoice_line_id', 'discount', type='float', 
            string='Discount (%)', digits_compute=dp.get_precision('Account'), readonly=True),
        'invoice_line_tax_id': fields.related('invoice_line_id', 'invoice_line_tax_id', relation='account.tax',
            type='many2many', string='Taxes', domain=[('parent_id','=',False)], readonly=True),   
        'service_period': fields.related('invoice_line_id', 'service_period', 
            type='char', size=23, string='Service Period'), 
        'service_period_section': fields.char('Service Period Section', size=23),
        'note': fields.text('Notes'),
        'company_id': fields.related('invoice_id', 'company_id', relation='res.company',
            type='many2one',string='Company', store=True, readonly=True),
    }
    _defaults = {
        'type': 'heading',
    }

