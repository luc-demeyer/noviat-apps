# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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

from openerp.tools.translate import _
from openerp.osv import fields, orm
import re
import time
import base64
from StringIO import StringIO
from lxml import etree
from openerp import tools
import logging
_logger = logging.getLogger(__name__)


class account_payment_make_payment(orm.TransientModel):
    _inherit = 'account.payment.make.payment'

    def launch_wizard(self, cr, uid, ids, context=None):
        """
        Search for a wizard to launch according to the type.
        Confirm the order without wizard if type is manual.
        """
        if context is None:
            context = {}
        obj_payment_order = self.pool['payment.order']
        obj_model = self.pool['ir.model.data']
        obj_act = self.pool['ir.actions.act_window']
        order = obj_payment_order.browse(
            cr, uid, context['active_id'], context)
        payment_type = order.mode and order.mode.type or 'manual'
        gw = obj_payment_order.get_wizard(payment_type)
        if (not gw) or (payment_type == 'manual'):
            obj_payment_order.set_done(
                cr, uid, [context['active_id']], context)
            return {'type': 'ir.actions.act_window_close'}

        # add support community modules using the
        # payment gateway wizard plugin
        module, wizard = gw
        result = obj_model._get_id(cr, uid, module, wizard)
        wiz_id = obj_model.read(cr, uid, [result], ['res_id'])[0]['res_id']
        if payment_type != 'iso20022':
            return_act = obj_act.read(cr, uid, [wiz_id])[0]
            return_act.update({'context': context})
            return return_act

        # generate ISO 20022 XML
        data = self.generate_pain(cr, uid, context)
        apc_id = self.pool.get('account.pain.create').create(cr, uid, data)
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(
            cr, uid,
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'account_pain_save_view')])
        resource_id = obj_model.read(
            cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'name': _('The ISO 20022 payment file has been created'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.pain.create',
            'res_id': apc_id,
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

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
        payment_mode = payment.mode
        pain_fname = re.sub('\W', '_', payment.reference).lower() + '.xml'
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not (payment_mode.bank_id.bank_bic
                or payment_mode.bank_id.bank.bic):
            raise orm.except_orm(
                _('Configuration Error!'),
                _("Please fill in the BIC code of the Bank "
                  "Debtor Account for this Payment Order!"))
        if not payment.line_ids:
            raise orm.except_orm(
                _('Data Error!'),
                _("Your Payment Order does not contain "
                  "payment instructions!"))

        # create XML
        ns_map = {
            None: 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        }
        pain = etree.Element('Document', nsmap=ns_map)
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
        CtrlSum.text = '%.2f' % payment.total_line_amount
        InitgPty = etree.SubElement(GrpHdr, 'InitgPty')
        Nm = etree.SubElement(InitgPty, 'Nm')
        Nm.text = company.name
        if payment_mode.initgpty_id:
            Id = etree.SubElement(InitgPty, 'Id')
            OrgId = etree.SubElement(Id, 'OrgId')
            Othr = etree.SubElement(OrgId, 'Othr')
            Id = etree.SubElement(Othr, 'Id')
            Id.text = payment_mode.initgpty_id
            if payment_mode.initgpty_issr:
                Issr = etree.SubElement(Othr, 'Issr')
                Issr.text = payment_mode.initgpty_issr
        # PaymentInformation
        payment_method = 'TRF'
        for line in payment.line_ids:

            if not line.amount:
                raise orm.except_orm(
                    _('Payment Instruction Error!'),
                    _('Payment Instruction Error in Payment Line %s.\n'
                      'Please fill in the transaction amount!'
                      ) % line.name)
            if not (line.bank_id and line.bank_id.acc_number):
                raise orm.except_orm(
                    _('Payment Instruction Error!'),
                    _("Unsupported Payment Instruction in Payment Line %s.\n"
                      "Please fill in the bank account number of the "
                      "Creditor for this Payment Line!"
                      ) % line.name)

            if payment.date_prefered == 'now':
                execution_date = time.strftime('%Y-%m-%d')
            elif payment.date_prefered == 'fixed':
                execution_date = payment.date_scheduled
            elif payment.date_prefered == 'due':
                if not line.date:
                    if line.ml_maturity_date:
                        execution_date = line.ml_maturity_date
                    else:
                        execution_date = time.strftime('%Y-%m-%d')
                else:
                    execution_date = line.date
            else:
                raise orm.except_orm(
                    _('Unsupported Payment Order Option!'),
                    _("Please ensure that the 'Preferred date' is equal "
                      "to 'Due date', 'Directly' or 'Fixed date'!"))
            if execution_date < time.strftime('%Y-%m-%d'):
                execution_date = time.strftime('%Y-%m-%d')
            if line.date != execution_date:
                note += _(
                    "\nThe Payment Date on Payment "
                    "Line %s has been changed."
                    ) % line.name
                payment_line_obj.write(
                    cr, uid, line.id, {'date': execution_date})

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
                if line.currency.name == 'EUR' \
                        or payment_mode.journal.currency == 'EUR':
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
                IBAN.text = payment_mode.bank_id.iban.upper().replace(' ', '')
                DbtrAgt = etree.SubElement(PmtInf, 'DbtrAgt')
                FinInstnId = etree.SubElement(DbtrAgt, 'FinInstnId')
                BIC = etree.SubElement(FinInstnId, 'BIC')
                BIC.text = re.sub(
                    '\s', '',
                    payment_mode.bank_id.bank_bic.upper()
                    or payment_mode.bank_id.bank.bic.upper())
                ChrgBr = etree.SubElement(PmtInf, 'ChrgBr')
                ChrgBr.text = line.bank_id.charge_bearer or 'SLEV'
                CdtTrfTxInf = etree.SubElement(PmtInf, 'CdtTrfTxInf')
                PmtId = etree.SubElement(CdtTrfTxInf, 'PmtId')
                EndToEndId = etree.SubElement(PmtId, 'EndToEndId')
                EndToEndId.text = line.name
                Amt = etree.SubElement(CdtTrfTxInf, 'Amt')
                InstdAmt = etree.SubElement(
                    Amt, 'InstdAmt', Ccy=line.currency.name)
                InstdAmt.text = '%.2f' % line.amount_currency
                # to be completed with other countries allowing
                # payments without BIC
                if line.bank_id.iban[0:2].upper() not in ['BE']:
                    if not (line.bank_id.bank_bic or line.bank_id.bank.bic):
                        raise orm.except_orm(
                            _('Configuration Error!'),
                            _("Unsupported Payment Instruction "
                              "in Payment Line %s.\n"
                              "Please fill in the BIC code of the Bank "
                              "Creditor Account for this Payment Line!"
                              ) % line.name)
                if line.bank_id.bank_bic or line.bank_id.bank.bic:
                    CdtrAgt = etree.SubElement(CdtTrfTxInf, 'CdtrAgt')
                    FinInstnId = etree.SubElement(CdtrAgt, 'FinInstnId')
                    BIC = etree.SubElement(FinInstnId, 'BIC')
                    BIC.text = re.sub(
                        '\s', '',
                        (line.bank_id.bank_bic or line.bank_id.bank.bic
                         ).upper())
                Cdtr = etree.SubElement(CdtTrfTxInf, 'Cdtr')
                Nm = etree.SubElement(Cdtr, 'Nm')
                Nm.text = line.partner_id.name
                CdtrAcct = etree.SubElement(CdtTrfTxInf, 'CdtrAcct')
                Id = etree.SubElement(CdtrAcct, 'Id')
                IBAN = etree.SubElement(Id, 'IBAN')
                IBAN.text = line.bank_id.iban.upper().replace(' ', '')
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
                            raise orm.except_orm(
                                _('Payment Instruction Error!'),
                                _("Unsupported Structured Communication "
                                  "in Payment Line %s.\n"
                                  "Only the Belgian Structured Communication "
                                  "format (BBA) is supported in the current "
                                  "release of the ISO 20022 payment module!"
                                  ) % line.name)
                        Ref = etree.SubElement(CdtrRefInf, 'Ref')
                        Ref.text = comm
                    else:
                        raise orm.except_orm(
                            _('Configuration Error!'),
                            _("Unsupported Communication Type "
                              "in Payment Line %s.\n"
                              ) % line.name)
        pain_data = etree.tostring(
            pain, encoding='UTF-8', xml_declaration=True, pretty_print=True)
        # validate the generated XML schema
        xsd = tools.file_open('account_pain/xsd/pain.001.001.03.xsd')
        xmlschema_doc = etree.parse(xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        xml_to_validate = StringIO(pain_data)
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
            _logger.error(
                'The generated XML file does not fit the required schema !')
            _logger.error(tools.ustr(xmlschema.error_log.last_error))
            error = xmlschema.error_log[0]
            raise orm.except_orm(
                _('The generated XML file does not fit the required schema !'
                  ), error.message)

        if note:
            note = _('Warning:\n') + note

        return {
            'pain_data': pain_data,
            'pain_fname': pain_fname,
            'note': note}


class account_pain_create(orm.TransientModel):
    _name = 'account.pain.create'
    _description = 'ISO 20022 payment file'

    _columns = {
        'pain_data': fields.binary(
            'Payment File', required=True, readonly=True),
        'pain_fname': fields.char(
            'Filename', size=128, required=True),
        'note': fields.text('Remarks'),
    }
