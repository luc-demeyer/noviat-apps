# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
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
import re
import time
import base64
from StringIO import StringIO
from lxml import etree
import tools
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

from operator import itemgetter
class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def amount_to_pay(self, cr, uid, ids, name, arg={}, context=None):
        """ Return the amount still to pay regarding all the payment orders
        (excepting cancelled orders)"""
        if not ids:
            return {}
        cr.execute("""SELECT ml.id,
                    CASE WHEN ml.amount_currency < 0
                        THEN - ml.amount_currency
                        ELSE ml.credit
                    END -
                    (SELECT coalesce(sum(amount_currency),0)
                        FROM payment_line pl
                            INNER JOIN payment_order po
                                ON (pl.order_id = po.id)
                        WHERE move_line_id = ml.id
                        AND po.state != 'cancel') AS amount
                    FROM account_move_line ml
                    WHERE id IN %s""", (tuple(ids),))
        r = dict(cr.fetchall())
        return r

    def _to_pay_search(self, cr, uid, obj, name, args, context=None):
        if not args:
            return []
        line_obj = self.pool.get('account.move.line')
        query = line_obj._query_get(cr, uid, context={})
        where = ' and '.join(map(lambda x: '''(SELECT
        CASE WHEN l.amount_currency < 0
            THEN - l.amount_currency
            ELSE l.credit
        END - coalesce(sum(pl.amount_currency), 0)
        FROM payment_line pl
        INNER JOIN payment_order po ON (pl.order_id = po.id)
        WHERE move_line_id = l.id
        AND po.state != 'cancel'
        ) %(operator)s %%s ''' % {'operator': x[1]}, args))
        sql_args = tuple(map(itemgetter(2), args))

        cr.execute(('''SELECT id
            FROM account_move_line l
            WHERE account_id IN (select id
                FROM account_account
                WHERE type in %s AND active)
            AND reconcile_id IS null
            AND credit > 0
            AND ''' + where + ' and ' + query), (('payable','receivable'),)+sql_args ) # fix Noviat to include sale refunds 

        res = cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', map(lambda x:x[0], res))]

    _columns = {
        'amount_to_pay': fields.function(amount_to_pay, method=True,
            type='float', string='Amount to pay', fnct_search=_to_pay_search),
    }

account_move_line()    

class payment_order_create(osv.osv_memory):
    _inherit = 'payment.order.create'
    
    """
    Override the search_entries & fields_view_get methods of the account_payment payment.order.create object
    """
    def search_entries(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, [], context=context)[0]
        search_due_date = data['duedate']
        # Search for move line to pay:
        domain = [('reconcile_id', '=', False), ('account_id.type', 'in', ['payable', 'receivable']), ('amount_to_pay', '>', 0)]  # update Noviat
        domain = domain + ['|', ('date_maturity', '<=', search_due_date), ('date_maturity', '=', False)]
        domain = domain + [('journal_id.type', 'in', ['purchase', 'sale_refund'])] # update Noviat
        line_ids = line_obj.search(cr, uid, domain, context=context)
        context.update({'line_ids': line_ids})
        model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'view_create_payment_order_lines')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {'name': _('Populate Payment'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
        }
        
    """
    add context to 'entries' field for use in account.move.line
    """
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(payment_order_create, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context and 'line_ids' in context:
            view_obj = etree.XML(res['arch'])           
            fields = view_obj.findall('.//field')
            for field in fields:
                if field.tag == 'field':
                    if field.get('name') == 'entries':
                        # add context for use in account.move.line
                        field.set('context', "{'account_payment':'1', 'view_mode':'tree'}")
                        field.set('colspan', '4')
                        field.set('height', '300')
                        field.set('width', '800')
            res['arch'] = etree.tostring(view_obj)
        return res
        
payment_order_create()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        if context.get('account_payment', False):
            model_data_ids = mod_obj.search(cr, uid,[('model', '=', 'ir.ui.view'), ('name', '=', 'view_move_line_tree_account_pain')], context=context)
            view_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']        
        return super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
    
account_move_line()

class account_payment_make_payment(osv.osv_memory):
    _inherit = 'account.payment.make.payment'

    def launch_wizard(self, cr, uid, ids, context=None):
        """
        Search for a wizard to launch according to the type.
        If type is manual. just confirm the order.
        """
        if context is None:
            context = {}
        obj_payment_order = self.pool.get('payment.order')
        obj_model = self.pool.get('ir.model.data')
        obj_act = self.pool.get('ir.actions.act_window')
        order = obj_payment_order.browse(cr, uid, context['active_id'], context)
        type = order.mode and order.mode.type or 'manual'
        gw = obj_payment_order.get_wizard(type)
        if (not gw) or (type == 'manual'):
            obj_payment_order.set_done(cr, uid, [context['active_id']], context)
            return {'type': 'ir.actions.act_window_close'}
        module, wizard = gw
        result = obj_model._get_id(cr, uid, module, wizard)
        id = obj_model.read(cr, uid, [result], ['res_id'])[0]['res_id']
        return_act = obj_act.read(cr, uid, [id])[0]
        return_act.update({'context': context})
        return return_act

account_payment_make_payment()

class account_pain_create(osv.osv_memory):
    _name = 'account.pain.create'
    _description = 'ISO 20022 payment file'
    
    def _pain_data(self, cr, uid, context):       
        return context['data']['pain_data']

    def _pain_fname(self, cr, uid, context):       
        return context['data']['pain_fname']

    def _pain_note(self, cr, uid, context):       
        return context['data']['pain_note']

    _columns = {
        'pain_data': fields.binary('Payment File', required=True, readonly=True),
        'pain_fname': fields.char('Filename', size=128, required=True),
        'note':fields.text('Remarks'),
        }
    _defaults={
        'pain_data': _pain_data,
        'pain_fname': _pain_fname,
        'note': _pain_note,
        }
    
    def view_init(self, cr , uid , fields_list, context=None):
        if context is None:
            context = {}
        payment_obj = self.pool.get('payment.order')
        if context.get('active_id',False):
            if payment_obj.browse(cr, uid, context['active_id']).state == 'draft':
                raise osv.except_osv(_('Error'), _('You cannot create payment files on Draft Payment Orders !'))
            pass
        self.generate_pain(cr, uid, context)

    def format_comm(self, comm):
        bbacomm = re.sub('\D', '', comm)
        if len(bbacomm) == 12:
            base = int(bbacomm[:10])
            mod = base % 97 or 97      
            if mod == int(bbacomm[-2:]):
                return bbacomm
        return False
    
    def generate_pain(self, cr, uid, context):
        if not context:
            context = {}
        active_id = context.get('active_id', [])
       
        payment_obj = self.pool.get('payment.order')
        payment_line_obj = self.pool.get('payment.line')
        attachment_obj = self.pool.get('ir.attachment')
        payment_line_obj = self.pool.get('payment.line')
        note = ''
        
        payment = payment_obj.browse(cr, uid, active_id, context=context)
        pain_fname = re.sub('\W', '_', payment.reference).lower() + '.xml'
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        company_nr = re.sub('\D', '', company.partner_id.vat)
        if len(company_nr) != 10:
            raise osv.except_osv(_('Configuration Error!'),
                _("Please check if the VAT field of your Company's Partner record is filled in correctly!"))
        if not payment.mode.bank_id.bank.bic:
            raise osv.except_osv(_('Configuration Error!'),
                _("Please fill in the BIC code of the Bank Debtor Account for this Payment Order!"))
        if not payment.line_ids:
             raise osv.except_osv(_('Data Error!'),
                _("Your Payment Order does not contain payment instructions!"))       
        if payment.mode.journal.currency.name != 'EUR':
            raise osv.except_osv(_('Payment Order Error!'),
                _('Only payments from a EURO bank account are supported in the current release '   \
                  'of the ISO 20022 payment module!'))       
    
        # create XML
        ns_map = {
            None: 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        }
        pain = etree.Element('Document', nsmap = ns_map)
        CstmrCdtTrfInitn = etree.SubElement(pain, 'CstmrCdtTrfInitn')
        # GroupHeader
        GrpHdr = etree.SubElement(CstmrCdtTrfInitn, 'GrpHdr')
        MsgId = etree.SubElement(GrpHdr, 'MsgId')
        MsgId.text = payment.reference
        CreDtTm = etree.SubElement(GrpHdr, 'CreDtTm')
        CreDtTm.text = time.strftime('%Y-%m-%dT%H:%M:%S')
        NbOfTxs = etree.SubElement(GrpHdr, 'NbOfTxs')
        NbOfTxs.text = str(len(payment.line_ids))
        CtrlSum = etree.SubElement(GrpHdr, 'CtrlSum')
        CtrlSum.text = '%.2f' % payment.total
        InitgPty = etree.SubElement(GrpHdr, 'InitgPty')
        Nm = etree.SubElement(InitgPty, 'Nm')
        Nm.text = company.name
        Id = etree.SubElement(InitgPty, 'Id')
        OrgId = etree.SubElement(Id, 'OrgId')
        Othr = etree.SubElement(OrgId, 'Othr')
        Id = etree.SubElement(Othr, 'Id')
        Id.text = company_nr
        Issr = etree.SubElement(Othr, 'Issr')
        Issr.text = 'KBO-BCE'
        # PaymentInformation
        payment_method = 'TRF'
        for line in payment.line_ids:
            if line.currency.name != 'EUR':
                raise osv.except_osv(_('Payment Instruction Error!'),
                    _('Unsupported Payment Instruction in Payment Line %s.\n'         \
                      'Only payments in EURO are supported in the current release '   \
                      'of the ISO 20022 payment module!') % line.name)
            if not line.amount:
                raise osv.except_osv(_('Payment Instruction Error!'),
                    _('Payment Instruction Error in Payment Line %s.\n'               \
                      'Please fill in the transaction amount!') %line.name)
            if not (line.bank_id and line.bank_id.iban):
                raise osv.except_osv(_('Payment Instruction Error!'),
                    _('Unsupported Payment Instruction in Payment Line %s.\n'    \
                      'Please fill in the IBAN number of the Bank Creditor Account for this Payment Line!') % line.name)            
    
            if payment.date_prefered == 'now':
                execution_date = time.strftime('%Y-%m-%d')
            elif payment.date_prefered == 'fixed':
                execution_date = payment.date_scheduled
            elif payment.date_prefered == 'due':
                if not line.date:
                    if line.ml_maturity_date:
                        excution_date = ml_maturity_date
                    else:
                        execution_date = time.strftime('%Y-%m-%d')      
                else:
                    execution_date = line.date
            else:
                raise osv.except_osv(_('Unsupported Payment Order Option!'),
                   _("Please ensure that the 'Preferred date' is equal to 'Due date', 'Directly' or 'Fixed date'!"))      
            if execution_date < time.strftime('%Y-%m-%d'):
                execution_date = time.strftime('%Y-%m-%d')
            if line.date != execution_date:
                note += _('\nThe Payment Date on Payment Line %s has been changed.') % line.name
                payment_line_obj.write(cr, uid, line.id, {'date': execution_date})
                
            PmtInf = etree.SubElement(CstmrCdtTrfInitn, 'PmtInf')
            PmtInfId = etree.SubElement(PmtInf, 'PmtInfId')
            PmtInfId.text = line.name
            PmtMtd = etree.SubElement(PmtInf, 'PmtMtd')
            PmtMtd.text = payment_method
            BtchBookg = etree.SubElement(PmtInf, 'BtchBookg')
            BtchBookg.text = 'false'
            if payment_method == 'TRF':
                PmtTpInf = etree.SubElement(PmtInf, 'PmtTpInf')
                InstrPrty = etree.SubElement(PmtTpInf, 'InstrPrty')
                InstrPrty.text = 'NORM'
                SvcLvl = etree.SubElement(PmtTpInf, 'SvcLvl')
                Cd = etree.SubElement(SvcLvl, 'Cd')      
                Cd.text = 'SEPA'
                ReqdExctnDt = etree.SubElement(PmtInf, 'ReqdExctnDt')
                ReqdExctnDt.text = execution_date
                Dbtr = etree.SubElement(PmtInf, 'Dbtr')
                Nm = etree.SubElement(Dbtr, 'Nm')            
                Nm.text = company.name
                DbtrAcct = etree.SubElement(PmtInf, 'DbtrAcct')
                Id = etree.SubElement(DbtrAcct, 'Id')
                IBAN = etree.SubElement(Id, 'IBAN')
                IBAN.text = payment.mode.bank_id.iban.upper().replace(' ','')
                DbtrAgt = etree.SubElement(PmtInf, 'DbtrAgt')
                FinInstnId = etree.SubElement(DbtrAgt, 'FinInstnId')
                BIC = etree.SubElement(FinInstnId, 'BIC')
                BIC.text = re.sub('\s','',payment.mode.bank_id.bank.bic.upper())
                ChrgBr = etree.SubElement(PmtInf, 'ChrgBr')
                ChrgBr.text = 'SLEV'
                CdtTrfTxInf = etree.SubElement(PmtInf, 'CdtTrfTxInf')
                PmtId = etree.SubElement(CdtTrfTxInf, 'PmtId')
                EndToEndId = etree.SubElement(PmtId, 'EndToEndId')            
                EndToEndId.text = line.name
                Amt = etree.SubElement(CdtTrfTxInf, 'Amt')
                InstdAmt = etree.SubElement(Amt, 'InstdAmt', Ccy='EUR')
                InstdAmt.text = '%.2f' % line.amount
                if line.bank_id.iban[0:2].upper() != 'BE':
                    CdtrAgt = etree.SubElement(CdtTrfTxInf, 'CdtrAgt')
                    if not line.bank_id.bank.bic:
                        raise osv.except_osv(_('Configuration Error!'),
                           _('Unsupported Payment Instruction in Payment Line %s.\n'    \
                             'Please fill in the BIC code of the Bank Creditor Account for this Payment Line!') % line.name)
                    FinInstnId = etree.SubElement(CdtrAgt, 'FinInstnId')
                    BIC = etree.SubElement(FinInstnId, 'BIC')
                    BIC.text = line.bank_id.bank.bic
                Cdtr = etree.SubElement(CdtTrfTxInf, 'Cdtr')
                Nm = etree.SubElement(Cdtr, 'Nm')
                Nm.text = line.partner_id.name
                CdtrAcct = etree.SubElement(CdtTrfTxInf, 'CdtrAcct')
                Id = etree.SubElement(CdtrAcct, 'Id')
                IBAN = etree.SubElement(Id, 'IBAN')
                IBAN.text = line.bank_id.iban.upper().replace(' ','')
                if line.communication:
                    comm = line.communication
                    if line.communication2:
                        comm += ' ' + line.communication2
                    RmtInf = etree.SubElement(CdtTrfTxInf, 'RmtInf')
                    if line.state == 'normal':
                        Ustrd = etree.SubElement(RmtInf, 'Ustrd')
                        Ustrd.text = comm
                    elif line.state == 'structured':
                        Strd = etree.SubElement(RmtInf, 'Strd')
                        CdtrRefInf = etree.SubElement(Strd, 'CdtrRefInf')
                        Tp = etree.SubElement(CdtrRefInf, 'Tp')
                        CdOrPrtry = etree.SubElement(Tp, 'CdOrPrtry')
                        Cd = etree.SubElement(CdOrPrtry, 'Cd')
                        Cd.text = 'SCOR'
                        Issr = etree.SubElement(Tp, 'Issr')
                        Issr.text = 'BBA'
                        comm = self.format_comm(line.communication)
                        if not comm:
                            raise osv.except_osv(_('Payment Instruction Error!'),
                               _('Unsupported Structured Communication in Payment Line %s.\n'                                  \
                                 'Only the Belgian Structured Communication format (BBA) is supported in the current release ' \
                                 'of the ISO 20022 payment module!') % line.name)
                        Ref = etree.SubElement(CdtrRefInf, 'Ref')
                        Ref.text = comm
                    else:
                        raise osv.except_osv(_('Configuration Error!'),
                            _('Unsupported Communication Type in Payment Line %s.\n') % line.name)
        pain_data = etree.tostring(pain, encoding='UTF-8', xml_declaration=True, pretty_print=True)   
        # validate the generated XML schema
        xsd = tools.file_open('account_pain/xsd/pain.001.001.03.xsd')
        xmlschema_doc = etree.parse(xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        xml_to_validate =  StringIO(pain_data)
        parse_result = etree.parse(xml_to_validate)
        if xmlschema.validate(parse_result):
            pain_data = base64.encodestring(pain_data)
            attachment_obj.create(cr, uid, {
                'name': pain_fname,
                'datas': pain_data,
                'datas_fname': pain_fname,
                'res_model': 'payment.order',
                'res_id': active_id,
                }, context=context)
            payment_obj.set_done(cr, uid, [active_id], context)
        else:
            _logger.error('The generated XML file does not fit the required schema !')
            _logger.error(tools.ustr(xmlschema.error_log.last_error))
            error = xmlschema.error_log[0]
            raise osv.except_osv(_('The generated XML file does not fit the required schema !'),
                error.message)      
    
        if note:       
            note = _('Warning:\n') + note
           
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'), ('name','=','account_pain_save_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        data = {'pain_data': pain_data, 'pain_fname': pain_fname, 'pain_note': note}
        context.update({'data': data})                       
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.pain.create',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

account_pain_create()

