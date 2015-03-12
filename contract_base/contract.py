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
from openerp.tools.translate import translate, _
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import netsvc
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class contract_category(orm.Model):
    _name = 'contract.category'
    _description = 'Contract Category'
    _order = 'code'
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'code': fields.char('Code', size=12, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'company_id':
            lambda s, cr, uid, ctx:
                s.pool.get('res.company')._company_default_get(
                    cr, uid, 'account.account', context=ctx),
        'active': True,
    }
    _sql_constraints = [
        ('code', 'unique (code)', 'The code must be unique !')
    ]


class contract_document(orm.Model):
    _name = 'contract.document'
    _description = 'Contracts'
    _order = 'name'

    def _get_contract_ref(self, cr, uid, context=None):
        if context.get('default_type') == 'sale':
            return self.pool.get('ir.sequence').next_by_code(cr,uid,'customer.contract.sequence')
        elif context.get('default_type') == 'purchase':
            return self.pool.get('ir.sequence').next_by_code(cr,uid,'supplier.contract.sequence')
        else:
            return False

    def _get_contract_type(self, cr, uid, context=None):
        return [('sale', 'Sale'), ('purchase', 'Purchase')] 

    def _get_company(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company_id = context.get('company_id', user.company_id.id)
        return company_id

    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        company_id = self._get_company(cr, uid, context)
        type = context.get('default_type', 'sale')
        res = self.pool.get('account.journal').search(cr, uid, 
            [('type', '=', type), ('company_id', '=', company_id)], limit=1)
        return res and res[0] or False

    def _get_currency(self, cr, uid, context=None):
        res = False
        journal_id = self._get_journal(cr, uid, context=context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            res = journal.currency and journal.currency.id or journal.company_id.currency_id.id
        return res

    def _get_invoices(self, cr, uid, ids, name, args, context=None):
        result = {}
        for contract in self.browse(cr, uid, ids, context=context):
            inv_ids = []
            for line in contract.contract_line:
                for billing in line.billing_ids:
                    if billing.invoice_id:
                        inv_ids.append(billing.invoice_id.id)
            inv_ids = list(set(inv_ids))
            inv_ids.sort(reverse=True)
            result[contract.id] = inv_ids
        return result

    def _get_contract_line(self, cr, uid, ids, context=None):
        result = []
        for contract_line in self.browse(cr, uid, ids):
            if contract_line.type == 'normal':
                result.append(contract_line.contract_id.id)
        return result

    def _update_mrc(self, cr, uid, ids):
        """ 
        Method to update recurring charges of a contract when
        a contract line has reached the 'billing_end' dates.
        """
        today = date.today()
        current_month_start = date(today.year, today.month, 1).isoformat()
        cl_obj = self.pool.get('contract.line')
        cl_ids = cl_obj.search(cr, uid, [('billing_type', '=', 'recurring'), ('billing_end' , '<', current_month_start)])
        if not cl_ids:
            return True
        else:
            # trigger _calc_mrc method
            cl_obj.write(cr, uid, cl_ids, {'billing_type': 'recurring'})
            return True
 
    def _calc_mrc(self, cline):
        """ 
        Method to calculate actual recurring charge of a contract
        Non-monthly charges are converted to a monthly amount for reporting purposes. 
        The result displayed is in the contract currency. 
        Billing lines beyond the billing_end date are not included in the calculation. 
        
        A monthly ir.cron job checks & updates the stored values in order to cope with contract lines that reach the 'billing_end' date.
        """
        if cline.billing_type != 'recurring':
            raise orm.except_orm(_('Error !'), _('Programming Error,  in _total_otc_mrc method !'))
        
        # eliminate contract lines terminated before the start of the current month
        if cline.billing_end:
            billing_end = datetime.strptime(cline.billing_end, '%Y-%m-%d').date()
            today = date.today()
            current_month_start = date(today.year, today.month, 1)
            if billing_end < date.today():
                return 0.0

        base_period = cline.billing_period_id.base_period
        multiplier = cline.billing_period_id.base_period_multiplier
        amount_period = cline.price_subtotal
        if base_period == 'month':
            return amount_period / multiplier
        elif base_period == 'year':
            return amount_period / (multiplier * 12)
        elif base_period == 'week':
            amount_daily = amount_period /(7 * multiplier)
            return (amount_daily * 365) / 12
        elif base_period == 'day':
            amount_daily = amount_period / multiplier
            return (amount_daily * 365) / 12
        else:
            raise NotImplementedError("A Billing Base Period with value %s is not supported" % base_period)

    def _total_otc_mrc(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for c in self.browse(cr, uid, ids):
            res[c.id] = {
                'total_otc': 0.0,
                'total_mrc': 0.0,
            }
            for cl in c.contract_line:
                if cl.type == 'normal':
                    if cl.billing_type == 'one_time':
                        res[c.id]['total_otc'] += cl.price_subtotal
                    elif cl.billing_type == 'recurring':
                        res[c.id]['total_mrc'] += self._calc_mrc(cl)
        return res

    _columns = {
        'name': fields.char('Contract Reference', size=128, required=True,
            readonly=True, states={'draft':[('readonly',False)]}),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic account', 
            domain=[('type','!=','view'),('parent_id', '!=', False)],
            readonly=True, states={'draft':[('readonly',False)]}),
        'categ_id': fields.many2one('contract.category', 'Contract Category',
            readonly=True, states={'draft':[('readonly',False)]}),
        'parent_id': fields.many2one('contract.document', 'Parent Contract',
                readonly=True, states={'draft':[('readonly',False)]}),
        'child_ids': fields.one2many('contract.document', 'parent_id', 'Child Contracts'),
        'user_id': fields.many2one('res.users', 'Contract Owner', required=True,
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True, 
            readonly=True, states={'draft':[('readonly',False)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, 
            readonly=True, states={'draft':[('readonly',False)]},
            help="Journal for invoices."),
        'type': fields.selection(_get_contract_type, 'Contract Type', required=True,
            readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([
            ('draft','Draft'),
            ('active','Active'),
            ('end','Terminated'),
            ('cancel', 'Cancelled'),
            ], 'State', required=True, readonly=True),    
        'date_start': fields.date('Date Start', required=True,
            readonly=True, states={'draft':[('readonly',False)]}),
        'date_end': fields.date('Date End',
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, 
            required=True, states={'draft':[('readonly',False)]}),
        'address_contact_id': fields.many2one('res.partner.address', 'Contact Address',
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'address_invoice_id': fields.many2one('res.partner.address', 'Invoice Address',
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}), 
        'payment_term': fields.many2one('account.payment.term', 'Payment Term',
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position',
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'invoice_ids': fields.function(_get_invoices, relation='account.invoice', type="many2many", string='Invoices',
            help="This is the list of invoices that are attached to contract lines."),
        'partner_ref': fields.char('Partner Contract Reference', size=64,
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]},
            help="You can use this field to record the reference assigned by your Supplier/Customer to this contract"),
        'note': fields.text('Notes'),
        'contract_line': fields.one2many('contract.line', 'contract_id', 'Contract Lines', 
            readonly=True, states={'draft': [('readonly', False)],'active':[('readonly',False)]}),
        'related_ids': fields.one2many('contract.document.related', 'contract_id', 'Related Contract Documents'),
        'company_id': fields.many2one('res.company', 'Company', required=True,
            readonly=True, states={'draft':[('readonly',False)],'active':[('readonly',False)]}),
        'active': fields.boolean('Active',
            readonly=True, states={'draft':[('readonly',False)]}),
        'total_otc': fields.function(_total_otc_mrc, string='Total OTC', type='float',
            digits_compute= dp.get_precision('Account'), help='Total One Time Charge',
            store={
                'contract.line': (_get_contract_line, ['price_subtotal', 'billing_type'], 20),
            },
            multi='all'),
        'total_mrc': fields.function(_total_otc_mrc, string='Total MRC', type='float',
            digits_compute= dp.get_precision('Account'), help='Total Monthly Recurring Charge',
            store={
                'contract.line': (_get_contract_line, ['price_subtotal', 'billing_type', 'billing_end'], 20),
            },
            multi='all'),
    }
    _defaults = {
        'name': _get_contract_ref,
        'user_id': lambda s, cr, uid, ctx: uid,
        'type': 'sale',
        'state': 'draft',
        'company_id': _get_company,
        'journal_id': _get_journal,
        'currency_id': _get_currency,
        'active': True,
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        invoice_addr_id = False
        contact_addr_id = False
        partner_payment_term = False
        fiscal_position = False

        addresses = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
        contact_addr_id = addresses['contact']
        invoice_addr_id = addresses['invoice']
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        fiscal_position = partner.property_account_position and partner.property_account_position.id or False
        partner_payment_term = partner.property_payment_term and partner.property_payment_term.id or False

        result = {
            'address_contact_id': contact_addr_id,
            'address_invoice_id': invoice_addr_id,
            'payment_term': partner_payment_term,
            'fiscal_position': fiscal_position
        }
        return {'value': result}

    def action_confirm(self, cr, uid, ids, context):  
        return self.write(cr, uid, ids, {'state':'active'}, context=context)

    def action_end(self, cr, uid, ids, context):  
        return self.write(cr, uid, ids, {'state':'end'}, context=context)

    def action_cancel(self, cr, uid, ids, context):  
        return self.write(cr, uid, ids, {'state':'cancel'}, context=context)

    def action_draft(self, cr, uid, ids, context):  
        return self.write(cr, uid, ids, {'state':'draft'}, context=context)

    def _get_invoice_type(self, cr, uid, contract_type, context=None):
        if contract_type == 'sale':
            return 'out_invoice'
        elif contract_type == 'purchase':
            return 'in_invoice'
        else:
            raise NotImplementedError("Contract Type %s is not supported" % contract_type)

    def create_invoice(self, cr, uid, ids,
                       period_id=None, date_invoice=None, context=None):
        #_logger.warn('create_invoice, ids=%s, period_id=%s', ids, period_id)
        wf_service = netsvc.LocalService('workflow')  
        cl_obj = self.pool.get('contract.line')
        clb_obj = self.pool.get('contract.line.billing')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_print_obj = self.pool.get('account.invoice.line.print')

        for contract in self.browse(cr, uid, ids, context=context):
            if contract.state != 'active':
                continue

            lang = contract.partner_id.lang
            def xlat(src):
                return translate(cr, 'contract.py', 'code', lang, src) or src

            invoices = {}
            for cl in contract.contract_line:
                if cl.billing_result == 'none':
                    continue
                if cl.type == 'heading':
                    continue
                billings = cl.billing_ids
                clb_table = cl_obj.calc_billing_table(
                    cr, uid, [cl.id], date_invoice, context=context)
                for entry in clb_table:
                    # check if already entry in billings
                    matches = filter(lambda x: x['date'] == entry['date'] , billings)
                    if matches:
                        billed = filter(lambda x: x['billed'], matches)
                        if not billed:
                            if len(matches) > 1:
                                raise orm.except_orm(_('Error !'), _('Ambiguous billing table !'))
                            else:
                                if invoices.get(entry['date']):
                                    invoices[entry['date']] += [{'contract_line': cl, 'billing_id': matches[0].id, 'service_period': entry.get('service_period')}]
                                else:
                                    invoices[entry['date']] = [{'contract_line': cl, 'billing_id': matches[0].id, 'service_period': entry.get('service_period')}]
                    # else create entry
                    else:
                        clb_id = clb_obj.create(cr, uid, entry)
                        if invoices.get(entry['date']):
                            invoices[entry['date']] += [{'contract_line': cl, 'billing_id': clb_id, 'service_period': entry.get('service_period')}]
                        else:
                            invoices[entry['date']] = [{'contract_line': cl, 'billing_id': clb_id, 'service_period': entry.get('service_period')}]

            #_logger.warn('create_invoice, invoices=%s', invoices)

            for k,v in invoices.iteritems():
                """
                An invoice groups all invoice lines with the same billing date.
                """

                cls = [x['contract_line'] for x in v]
                billing_results = [cl.billing_result for cl in cls]
                clb_ids = [x['billing_id'] for x in v]
                inv_state = 'draft' in billing_results and 'draft' or 'open'
                inv_type = self._get_invoice_type(cr, uid, contract.type)
                inv_vals = inv_obj.onchange_partner_id(cr, uid, ids, inv_type, contract.partner_id.id,
                    date_invoice=date_invoice, payment_term=contract.payment_term, partner_bank_id=False, company_id=contract.company_id.id)['value']
                #_logger.warn('create_invoice, inv_vals=%s', inv_vals)
                inv_vals.update({
                    'name': contract.categ_id and ', '.join([contract.name, contract.categ_id.code]) or contract.name,
                    'origin': contract.name,
                    'type': inv_type,
                    'date_invoice': date_invoice,
                    'partner_id': contract.partner_id.id,
                    'period_id': period_id,
                    'journal_id': contract.journal_id.id,
                    'company_id': contract.company_id.id,
                    'currency_id': contract.currency_id.id,
                    })
                #_logger.warn('create_invoice, inv_vals=%s', inv_vals)
                inv_id = inv_obj.create(cr, uid, inv_vals, context=context)
                clb_obj.write(cr, uid, clb_ids, {'invoice_id': inv_id, 'billed': True})
                #_logger.warn('create_invoice, inv_id=%s', inv_id)     

                inv_lines = []            
                for entry in v:
                    #_logger.warn('entry = %s', entry)
                    cl = entry['contract_line']
                    billing_id = entry['billing_id']
                    inv_line = {
                        'contract_line': cl,
                        'section': cl.parent_id,
                        'service_period': entry.get('service_period'),
                    }
                    inv_lines.append(inv_line)

                # group/order lines by section and by service period and insert heading line 
                # when no corresponding heading line is available for a specific service period
                #_logger.warn('%s, create_invoice, inv_lines=%s', self._name, inv_lines)

                # step 1 : add generic 'nrc' and 'rc' sections to lines that don't belong to a section
                for inv_line in inv_lines:
                    inv_line['section'] = inv_line['section'] or inv_line['service_period'] and 'rc' or 'nrc'

                # step 2 : order lines by 1) section and 2) service period
                inv_lines.sort(key=lambda k: (k['section'],k['service_period']))

                #_logger.warn('%s, create_invoice, inv_lines=%s', self._name, inv_lines)
                # step 3 : add heading lines
                section_stack = [('empty','empty')]
                for inv_line in inv_lines:
                    section = inv_line['section']
                    service_period = inv_line['service_period']
                    section_tuple = (section, service_period)

                    # create heading line
                    if section_tuple != section_stack[-1]:
                        section_stack.append(section_tuple)
                        if isinstance(section, basestring): 
                            if section not in ['rc', 'nrc']:
                                raise NotImplementedError("'%s' : unsupported section !" %section)
                            cl_child = inv_line['contract_line']
                            heading_line_vals = {
                                'invoice_id': inv_id,
                                'contract_line_id': None,   
                                'name': section == 'nrc' and xlat('One Time Charges') or xlat('Recurring Charges'),
                                'sequence': cl_child.sequence, # use sequence number of first child
                                'type': 'heading',
                                'service_period_section': service_period,
                            }
                        else:
                            cl = inv_line['section']
                            heading_line_vals = {
                                'invoice_id': inv_id,
                                'contract_line_id': cl.id,   
                                'name': cl.name,
                                'sequence': cl.sequence,
                                'type': 'heading',
                                'service_period_section': service_period,
                                'hidden': cl.hidden,
                                'note': cl.note,
                            }
                        heading_line_id = inv_line_print_obj.create(cr, uid, heading_line_vals)
                        # To DO : add support for multiple levels of heading lines

                    # create invoice lines
                    cl = inv_line['contract_line']
                    inv_line_vals = {
                         'invoice_id': inv_id,
                         'name': cl.name,
                         'service_period': inv_line['service_period'],
                         'account_id': cl.account_id.id,
                         'price_unit': cl.price_unit,
                         'quantity': cl.quantity,
                         'note': cl.note,
                    }
                    if cl.product_id:
                        inv_line_vals.update({
                            'product_id': cl.product_id.id,
                            'uos_id': cl.uom_id.id,
                            'price_unit': cl.price_unit,
                        })
                    if cl.discount:
                        inv_line_vals['discount'] = cl.discount
                    if cl.analytic_account_id:
                        inv_line_vals['account_analytic_id'] = cl.analytic_account_id.id
                    if cl.tax_ids:
                        inv_line_vals['invoice_line_tax_id'] = [(6, 0, [x.id for x in cl.tax_ids])]
                    #_logger.warn('create_invoice, inv_line_vals=%s', inv_line_vals) 
                    inv_line_id = inv_line_obj.create(cr, uid, inv_line_vals)
                    
                    inv_line_print_vals = {
                        'invoice_id': inv_id,
                        'invoice_line_id': inv_line_id,
                        'contract_line_id': cl.id,
                        'name': cl.name,
                        'sequence': cl.sequence,
                        'type': 'normal',
                        'parent_id': heading_line_id,
                        'service_period_section': entry.get('service_period'),
                        'hidden': cl.hidden,
                        'note': cl.note,
                    }
                    #_logger.warn('create_invoice, inv_line_print_vals=%s', inv_line_print_vals) 
                    inv_line_print_id = inv_line_print_obj.create(cr, uid, inv_line_print_vals)                        

                inv_obj.button_compute(cr, uid, [inv_id])
                if inv_state == 'open':
                    wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)

        return True


class contract_line(orm.Model):
    _name = 'contract.line'
    _description = 'Contract Lines'
    _order = "contract_id, sequence asc"

    def _get_contract_line(self, cr, uid, ids, context=None):
        result = []
        for cl in self.browse(cr, uid, ids):
            if cl.type == 'normal':
                result.append(cl.id)
            def _parent_ids(rec):
                res = [rec.id]
                if rec.parent_id:
                    res += _parent_ids(rec.parent_id)
                return res
            if cl.parent_id:
                result += _parent_ids(cl.parent_id)
        return result

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
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
                taxes = tax_obj.compute_all(cr, uid, l.tax_ids, price, l.quantity, product=l.product_id, 
                    address_id=l.contract_id.address_invoice_id, partner=l.contract_id.partner_id)
                total += taxes['total']
                total_included += taxes['total_included']
            res[line.id] = total
            cur = line.contract_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def _calc_billing_end(self, cr, uid, billing_start, billing_period_id, billing_period_nbr):
        if billing_start:
            billing_start = datetime.strptime(billing_start, '%Y-%m-%d').date()
        billing_period = self.pool.get('billing.period').browse(cr, uid, billing_period_id)
        base_period = billing_period.base_period
        delta = billing_period.base_period_multiplier * billing_period_nbr
        billing_end = False
        if billing_start:
            if base_period == 'day':
                billing_end = billing_start + timedelta(delta-1)
            elif base_period == 'week':
                billing_end = billing_start + timedelta(7*delta-1)
            elif base_period == 'month':
                billing_end = billing_start + relativedelta(months=delta, days=-1)
            elif base_period == 'year':
                billing_end = billing_start + relativedelta(years=delta, days=-1)
        return billing_end and billing_end.isoformat() or billing_end

    def _billing_end(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.billing_type == 'one_time':
                res[line.id] = line.billing_start
            else:
                if line.billing_unlimited:
                    res[line.id] = False
                else:
                    billing_end = self._calc_billing_end(cr, uid, line.billing_start, line.billing_period_id.id, line.billing_period_nbr)
                    res[line.id] = billing_end
        return res

    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of contract lines."),
        'contract_id': fields.many2one('contract.document', 'Contract Reference', ondelete='cascade'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic account', 
            domain=[('type','!=','view'),('parent_id', '!=', False)]),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
        'product_id': fields.many2one('product.product', 'Product', ondelete='set null'),
        'account_id': fields.many2one('account.account', 'Account', domain=[('type','!=','view'), ('type', '!=', 'closed')],
            help="The income or expense account related to the selected product."),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Account')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', type='float',
            digits_compute= dp.get_precision('Account'), 
            store={
                'contract.line': (_get_contract_line, ['price_unit','tax_ids','quantity','discount'], 10),
            }),
        'quantity': fields.float('Quantity', required=True),
        'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Account')),
        'tax_ids': fields.many2many('account.tax', string='Taxes'),
        'type': fields.selection([
            ('heading','Section Heading'),
            ('normal','Normal'),
            ], 'Type', required=True),        
        'parent_id': fields.many2one('contract.line', 'Section',
            help="Use this field to order contract lines in sections whereby the parent_id contains section heading info."),
        'child_ids': fields.one2many('contract.line', 'parent_id', 'Section Lines'),
        'hidden': fields.boolean('Hidden',
            help='Use this flag to hide contract lines on the printed Invoice.'),
        # billing info
        'billing_type': fields.selection([
            ('recurring','Recurring Charge'),
            ('one_time','One Time Charge'),
            ], 'Billing Type'),  
        'billing_result': fields.selection([
            ('open','Open Invoice'),
            ('draft','Draft Invoice'),
            ('none','None'),
            ], 'Invoice State', required=True,
            help="State of the invoice created by the billing engine."
                 "\n'Draft' prevails in case of multiple lines with different Invoice States."
                 "\n'None' is used for invoice lines that are created manually."),  
        'prepaid': fields.boolean('Prepaid',
            help="Check this box for prepaid billing."),    
        'billing_start': fields.date('Billing Start Date'),
        'billing_end': fields.function(_billing_end, string='Billing End Date', type='date', readonly=True),
        'billing_period_id': fields.many2one('billing.period', 'Billing Periodicity'),
        'billing_unlimited': fields.boolean('Unlimited',
            help="Check this box for recurring billing with no determined end date."),
        'billing_period_nbr': fields.integer('Number of Periods'),
        'billing_ids': fields.one2many('contract.line.billing', 'contract_line_id', 'Billing History'),
        #
        'note': fields.text('Notes'),
        'company_id': fields.related('contract_id','company_id',type='many2one',relation='res.company',string='Company', store=True, readonly=True),
    }
    _defaults = {
        'discount': 0.0,
        'quantity': 1.0,
        'sequence': 10,
        'price_unit': 0.0,
        'type': 'normal',
        'prepaid': True,
        'billing_type': 'recurring',
        'billing_result': 'draft',        
    }

    def _check_billing_period_nbr(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.billing_type == 'recurring' and not line.billing_unlimited and line.billing_period_nbr <= 0:
                return False
        return True

    _constraints = [
    (_check_billing_period_nbr, '\nThe number of periods must be greater than zero !', ['billing_period_nbr'])
    ]

    def onchange_type(self, cr, uid, ids, type):
        if type == 'heading':
            return {'value':{'billing_type': None}}
        else:
            return {}

    def onchange_billing_unlimited(self, cr, uid, ids, billing_unlimited, context=None):
        if billing_unlimited: 
            return {'value':{'billing_end': False, 'billing_period_nbr': False}}
        else:
            return {}

    def onchange_billing_end(self, cr, uid, ids, billing_start, billing_period_id, billing_period_nbr, billing_unlimited, context=None):
        billing_end = False
        if ids:
            if not billing_unlimited and billing_period_nbr <= 0:
                raise orm.except_orm(_('Error !'), _('The number of periods must be greater than zero !'))
            billing_end = self._calc_billing_end(cr, uid, billing_start, billing_period_id, billing_period_nbr)
        return {'value':{'billing_end': billing_end}}

    def onchange_product_id(self, cr, uid, ids, product_id, contract_type,  
        partner_id, company_id, currency_id, fposition_id=False, context=None):
        #_logger.warn('onchange_product_id, product_id=%s, contract_type=%s, partner_id=%s, company_id=%s, currency_id=%s, fposition_id=%s', 
        #    product_id, contract_type, partner_id, company_id, currency_id, fposition_id)
        #_logger.warn('onchange_product_id, context=%s', context)
        if context is None:
            context = {}

        partner_obj = self.pool.get('res.partner')
        fpos_obj = self.pool.get('account.fiscal.position')
        product_obj = self.pool.get('product.product')
        company_obj = self.pool.get('res.company')
        curr_obj = self.pool.get('res.currency')

        company_id = company_id if company_id != None else context.get('company_id',False)
        context.update({'company_id': company_id})
        if not partner_id:
            raise orm.except_orm(_('No Partner Defined !'),_("You must first select a partner !"))
        if not product_id:
                return {'value': {'price_unit': 0.0}, 'domain':{'product_uom':[]}}
        partner = partner_obj.browse(cr, uid, partner_id, context=context)
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False

        product = product_obj.browse(cr, uid, product_id, context=context)
        company = company_obj.browse(cr, uid, company_id, context=context)
        currency = curr_obj.browse(cr, uid, currency_id, context=context)
        if company.currency_id.id != currency.id:
            multi_currency = True
        else:
            multi_currency = False

        if contract_type == 'sale':
            name = product_obj.name_get(cr, uid, [product.id], context=context)[0][1]
            billing_type = product.product_tmpl_id.billing_type_sale
            billing_result = product.product_tmpl_id.billing_result_sale
            billing_period_id = product.product_tmpl_id.billing_period_sale_id.id
            billing_unlimited = product.product_tmpl_id.billing_unlimited_sale
            billing_period_nbr = product.product_tmpl_id.billing_period_nbr_sale
            if not billing_type:
                billing_type = product.categ_id.billing_type_sale
                billing_result = product.categ_id.billing_result_sale
                billing_period_id = product.categ_id.billing_period_sale_id.id
                billing_unlimited = product.categ_id.billing_unlimited_sale
                billing_period_nbr = product.categ_id.billing_period_nbr_sale
            price_unit = product.list_price
            tax_ids = fpos_obj.map_tax(cr, uid, fpos, product.taxes_id)
            uom_id = product.uos_id.id or product.uom_id.id
            account_id = product.property_account_income.id
            if not account_id:
                account_id = product.categ_id.property_account_income_categ.id

        else:
            name = product.partner_ref
            billing_type = product.product_tmpl_id.billing_type_purchase
            billing_period_id = product.product_tmpl_id.billing_period_purchase_id.id
            billing_unlimited = product.product_tmpl_id.billing_unlimited_purchase
            billing_period_nbr = product.product_tmpl_id.billing_period_nbr_purchase
            if not billing_type:
                billing_type = product.categ_id.billing_type_purchase
                billing_period_id = product.categ_id.billing_period_purchase_id.id
                billing_unlimited = product.categ_id.billing_unlimited_purchase
                billing_period_nbr = product.categ_id.billing_period_nbr_purchase
            price_unit = product.standard_price
            tax_ids = fpos_obj.map_tax(cr, uid, fpos, product.supplier_taxes_id)
            uom_id = product.uom_id.id
            account_id = product.property_account_expense.id
            if not account_id:
                account_id = product.property_account_expense_categ.id

        if multi_currency:
            price_unit = price_unit * currency.rate

        value = {
            'name': name,
            'billing_type': billing_type,
            'billing_period_id': billing_period_id,
            'billing_unlimited': billing_unlimited,
            'billing_period_nbr': billing_period_nbr,
            'price_unit': price_unit,
            'tax_ids': tax_ids,
            'uom_id': uom_id,
            'account_id': account_id,
        }
        if contract_type == 'sale': 
            value['billing_result'] = billing_result
        #_logger.warn('onchange_product_id, value=%s', value)
        return {'value': value}

    # Set the tax field according to the account and the fiscal position
    def onchange_account_id(self, cr, uid, ids, product_id, partner_id,
                            contract_type, fposition_id, account_id):
        #_logger.warn('%s, onchange_account_id, product_id=%s, partner_id=%s, contract_type=%s, fposition_id=%s, account_id=%s',
        #    self._name, product_id, partner_id, contract_type, fposition_id, account_id)
        if not account_id:
            return {}
        unique_tax_ids = []
        fpos = fposition_id and self.pool.get('account.fiscal.position').browse(cr, uid, fposition_id) or False
        account = self.pool.get('account.account').browse(cr, uid, account_id)
        if not product_id:
            taxes = account.tax_ids
            unique_tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
        else:
            # force user chosen account in context to allow onchange_product_id()
            # to fallback to the this accounts in case product has no taxes defined.
            context = {'account_id': account_id}
            company = account.company_id
            product_change_result = self.onchange_product_id(cr, uid, ids, product_id, contract_type,
                partner_id, company.id, company.currency_id.id, fposition_id=fposition_id, context=context)
            if product_change_result and 'value' in product_change_result and 'tax_ids' in product_change_result['value']:
                unique_tax_ids = product_change_result['value']['tax_ids']
        return {'value':{'tax_ids': unique_tax_ids}}

    def calc_billing_table(self, cr, uid, contract_line_ids,
                           date_invoice=None, context=None):
        clb_obj = self.pool.get('contract.line.billing')
        clb_tables = []

        for cline in self.browse(
                cr, uid, contract_line_ids, context=context):
            clb_table = {'contract_line_id': cline.id}
            billing_start = datetime.strptime(
                cline.billing_start, '%Y-%m-%d').date()
            date_end = date_invoice and \
                datetime.strptime(date_invoice, '%Y-%m-%d').date() or \
                date.today()
            if cline.billing_end:
                cl_billing_end = datetime.strptime(
                    cline.billing_end, '%Y-%m-%d').date()
                if date_end > cl_billing_end:
                    date_end = cl_billing_end
            #_logger.warn('calc_billing_table, billing_start=%s, date_invoice=%s, date_end=%s', billing_start, date_invoice, date_end.isoformat())

            if cline.billing_type == 'one_time':
                clb_table.update({
                    'number': 1,
                    'date': billing_start.isoformat(),
                })
                clb_tables.append(clb_table)

            elif cline.billing_type == 'recurring':
                base_period = cline.billing_period_id.base_period
                multiplier = cline.billing_period_id.base_period_multiplier
                if base_period == 'day':
                    number = int(
                        (date_end - billing_start).days / multiplier + 1)
                elif base_period == 'week':
                    d_start = billing_start.day
                    d = date_end.day
                    x = 1 if (d_start <= d) else 0
                    number = int(
                        (date_end - billing_start).days /
                        (7 * multiplier) + x)
                elif base_period == 'month':
                    d_start = billing_start.day
                    # get last day of the month
                    month_end = date_end + relativedelta(day=31)
                    # include all service periods starting up to
                    # the end of the 'date_end' month
                    x = 1 if (d_start <= month_end.day) else 0
                    number = int(
                        (12 * (date_end.year - billing_start.year) +
                        date_end.month - billing_start.month)/multiplier + x)
                elif base_period == 'year':
                    diff_year = date_end.year - billing_start.year
                    if not diff_year:
                        current_year_renewal = True
                    else:
                        current_year_renewal = False
                    if multiplier <= diff_year:
                        mod = diff_year % multiplier
                        if not mod:
                            current_year_renewal = True
                    if current_year_renewal:
                        d_start = billing_start.timetuple().tm_yday
                        # get last day of the month
                        month_end = date_end + relativedelta(day=31)
                        d = month_end.timetuple().tm_yday
                        # include all service periods starting up to
                        # the end of the 'date_end' month
                        x = 1 if (d_start <= d) else 0
                    else:
                        x = 1
                    number = int(diff_year / multiplier + x)

                for i in range(number):
                    if base_period == 'day':
                        billing_date = billing_start + timedelta(i)
                        if cline.prepaid:
                            service_period = '%s - %s' %(billing_date.isoformat(), (billing_date + timedelta(multiplier - 1)).isoformat())
                        else:
                            service_period = '%s - %s' %((billing_date - timedelta(multiplier)).isoformat(), (billing_date - timedelta(1)).isoformat())
                    elif base_period == 'week':
                        billing_date = (billing_start + timedelta(i) * 7 * multiplier)
                        if cline.prepaid:
                            service_period = '%s - %s' %(billing_date.isoformat(), (billing_date + timedelta(7*multiplier - 1)).isoformat())
                        else:
                            service_period = '%s - %s' %((billing_date - timedelta(7*multiplier)).isoformat(), (billing_date - timedelta(1)).isoformat())
                    elif base_period == 'month':
                        billing_date = billing_start + relativedelta(months=i*multiplier)
                        if cline.prepaid:
                            service_period = '%s - %s' %(billing_date.isoformat(), (billing_date + relativedelta(months=multiplier, days= -1)).isoformat())
                        else:
                            service_period = '%s - %s' %((billing_date - relativedelta(months=multiplier)).isoformat(), (billing_date - timedelta(1)).isoformat())
                    elif base_period == 'year':
                        billing_date = billing_start + relativedelta(years=i*multiplier)
                        if cline.prepaid:
                            service_period = '%s - %s' %(billing_date.isoformat(), (billing_date + relativedelta(years=multiplier, days= -1)).isoformat())
                        else:
                            service_period = '%s - %s' %((billing_date - relativedelta(years=multiplier)).isoformat(), (billing_date - timedelta(1)).isoformat())

                    entry = clb_table.copy()
                    entry.update({
                        'number': i + 1,
                        'date': billing_date.isoformat(),
                        'service_period': service_period,
                    })
                    #_logger.warn('clb_table=%s', entry)
                    clb_tables += [entry]

        #_logger.warn('calc_billing_table, return clb_tables=%s', clb_tables)
        return clb_tables 

    def generate_billing_table(self, cr, uid, ids, context=None):    
        clb_obj = self.pool.get('contract.line.billing')
        for cline in self.browse(cr, uid, ids, context=context):
            billing_start = datetime.strptime(cline.billing_start, '%Y-%m-%d').date()
            today = date.today()
            #_logger.warn('generate_billing_table, billing_start=%s, today=%s', billing_start, today)
            if billing_start > today:
                raise orm.except_orm(_('Warning !'), _("No entries created since the billing hasn't started yet !"))
            billing_ids = cline.billing_ids
            if billing_ids:
                for billing_id in cline.billing_ids:
                    if billing_id.billed:
                        raise orm.except_orm(_('Warning !'), 
                            _("You cannot regenerate the billing table since some entries have been billed already '"))
                clb_obj.unlink(cr, uid, [x.id for x in billing_ids])
            clb_table = self.calc_billing_table(cr, uid, [cline.id], context=context)
            #_logger.warn('generate_billing_table, clb_table=%s', clb_table)
            for vals in clb_table:
                clb_obj.create(cr, uid, vals)
        return True    


class contract_line_billing(orm.Model):
    _name = 'contract.line.billing'
    _description = 'Contract Line Billing History'
    _order = 'number'

    _columns = {
        'number': fields.integer('Number'),
        'date': fields.date('Billing Date', required=True),
        'contract_line_id': fields.many2one('contract.line', 'Contract Line', ondelete='cascade'),
        'billed': fields.boolean('Billed'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'service_period': fields.char('Service Period', size = 23),
        'note': fields.text('Notes'),
    }

    def onchange_invoice_id(self, cr, uid, ids, invoice_id):
        #_logger.warn('onchange_invoice_id, invoice_id=%s', invoice_id)
        return {'value': {'billed': invoice_id and True or False}}


class contract_document_related(orm.Model):
    _name = 'contract.document.related'
    _description = 'Contracts - related documents'

    def _get_reference_model(self, cr, uid, context=None):
        ref_models = [
            ('sale.order', 'Sales Order'), 
            ('purchase.order', 'Purchase Order'),
        ]
        return ref_models

    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of contract lines."),
        'contract_id': fields.many2one('contract.document', 'Contract Reference', ondelete='cascade'),
        'document': fields.reference('Related Document', selection=_get_reference_model, required=True, size=128),
        'note': fields.text('Notes'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: