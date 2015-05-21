# -*- coding: utf-8 -*-
# noqa: skip pep8 control until this wizard is rewritten.
# flake8: noqa
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Adapted by Noviat to
#     - enforce correct vat number
#     - support negative balance
#     - assign amount of tax code 71-72 correclty to grid 71 or 72
#     - support Noviat tax code scheme
#     - support multiple accounting periods per VAT declaration
#     - add print button
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

import base64
from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.report import report_sxw
import logging
_logger = logging.getLogger(__name__)


class l10n_be_vat_declaration(orm.TransientModel):
    """ Periodical VAT Declaration """
    _name = "l10n_be.vat.declaration"
    _description = "Periodical VAT Declaration"

    def _get_xml_data(self, cr, uid, context=None):
        if context.get('file_save', False):
            return base64.encodestring(context['file_save'].encode('utf8'))
        return ''

    _columns = {
        'name': fields.char('File Name', size=32),
        'period_from': fields.many2one('account.period', 'Start Period', required=True),
        'period_to': fields.many2one('account.period', 'End Period', required=True),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code',
            domain=[('parent_id', '=', False)], required=True),
        'msg': fields.text('File created', size=64, readonly=True),
        'file_save': fields.binary('Save File'),
        'ask_restitution': fields.boolean('Ask Restitution',
            help='It indicates whether a resitution is to made or not?'),
        'ask_payment': fields.boolean('Ask Payment',
            help='It indicates whether a payment is to made or not?'),
        'client_nihil': fields.boolean('Last Declaration, no clients in client listing',
            help='Tick this case only if it concerns only the last statement '
                 'on the civil or cessation of activity: '
                 'no clients to be included in the client listing.'),
        'comments': fields.text('Comments'),
    }

    def _get_tax_code(self, cr, uid, context=None):
        obj_tax_code = self.pool.get('account.tax.code')
        obj_user = self.pool.get('res.users')
        company_id = obj_user.browse(cr, uid, uid, context=context).company_id.id
        tax_code_ids = obj_tax_code.search(cr, uid, [
            ('company_id', '=', company_id), ('parent_id', '=', False)
            ], context=context)
        return tax_code_ids and tax_code_ids[0] or False

    _defaults = {
        'msg': 'Save the File with '".xml"' extension.',
        'file_save': _get_xml_data,
        'name': 'vat_declaration.xml',
        'tax_code_id': _get_tax_code,
    }

    def _get_datas(self, cr, uid, ids, context=None):

        obj_tax_code = self.pool.get('account.tax.code')
        obj_acc_period = self.pool.get('account.period')
        obj_user = self.pool.get('res.users')
        obj_partner = self.pool.get('res.partner')

        if context is None:
            context = {}

        list_of_tags = [
            '00', '01', '02', '03', '44', '45', '46', '47', '48', '49',
            '54', '55', '56', '57', '59', '61', '62', '63', '64', '71',
            '72', '81', '82', '83', '84', '85', '86', '87', '88', '91',
        ]
        data_tax = self.browse(cr, uid, ids[0])

        if data_tax.tax_code_id:
            obj_company = data_tax.tax_code_id.company_id
        else:
            obj_company = obj_user.browse(cr, uid, uid, context=context).company_id
        vat_no = obj_company.partner_id.vat
        if not vat_no:
            raise orm.except_orm(_('Insufficient Data!'),
                _('No VAT number associated with your company.'))
        vat_no = vat_no.replace(' ', '').upper()
        vat = vat_no[2:]

        tax_code_ids = obj_tax_code.search(cr, uid, [
            ('parent_id', 'child_of', data_tax.tax_code_id.id),
            ('company_id', '=', obj_company.id)], context=context)
        ctx = context.copy()
        data = self.read(cr, uid, ids)[0]
        tax_info = {}

        period_from = data_tax.period_from
        period_to = data_tax.period_to
        period_ids = [period_from.id, period_to.id]
        period_ids += obj_acc_period.search(cr, uid, [
            ('date_start', '>=', period_from.date_start),
            ('date_stop', '<=', period_to.date_stop),
            ('special', '=', False)])
        period_ids = list(set(period_ids))
        for period_id in period_ids:
            ctx['period_id'] = period_id  # added context here
            tax_period_info = obj_tax_code.read(cr, uid, tax_code_ids, ['code', 'name', 'sum_period'], context=ctx)
            for c in tax_period_info:
                c_amt = tax_info.get(c['code']) and tax_info[c['code']][1] or 0.0
                tax_info.update({c['code']: (c['name'], c_amt + c['sum_period'])})

        default_address = obj_partner.address_get(cr, uid, [obj_company.partner_id.id])
        default_address_id = default_address.get("default", obj_company.partner_id.id)
        address_id = obj_partner.browse(cr, uid, default_address_id, context)

        issued_by = vat_no[:2]
        comments = data['comments'] or ''

        send_ref = str(obj_company.partner_id.id) + period_from.date_start[5:7] + period_to.date_stop[:4]

        starting_month = period_from.date_start[5:7]
        ending_month = period_to.date_stop[5:7]
        year = period_to.date_stop[:4]
        quarter = str(((int(starting_month) - 1) / 3) + 1)

        if not address_id.email:
            raise orm.except_orm(_('Data Insufficient!'),
                _('No email address associated with the company.'))
        if not address_id.phone:
            raise orm.except_orm(_('Data Insufficient!'),
                _('No phone associated with the company.'))
        xml_dict = {
            'issued_by': issued_by,
            'vat_no': vat_no,
            'only_vat': vat_no[2:],
            'cmpny_name': obj_company.name,
            'address': "%s %s" % (address_id.street or "", address_id.street2 or ""),
            'post_code': address_id.zip or "",
            'city': address_id.city or "",
            'country_code': address_id.country_id and address_id.country_id.code or "",
            'email': address_id.email or "",
            'phone': address_id.phone.replace('.', '').replace('/', '').replace('(', '').replace(')', '').replace(' ', ''),
            'send_ref': send_ref,
            'quarter': quarter,
            'month': starting_month,
            'period_start': period_from.code,
            'period_end': period_to.code,
            'ending_month': ending_month,
            'year': year,
            'client_nihil': (data['client_nihil'] and 'YES' or 'NO'),
            'ask_restitution': (data['ask_restitution'] and 'YES' or 'NO'),
            'ask_payment': (data['ask_payment'] and 'YES' or 'NO'),
            'comments': comments,
        }

        if tax_info.get('VI')[1] >= 0:
            tax_info['71'] = tax_info['VI']
        else:
            tax_info['72'] = tax_info['VI']
        cases_list = []
        for item in tax_info:
            if tax_info['91'][1] and ending_month != 12:
                #the tax code 91 can only be send for the declaration of December
                raise orm.except_orm(_('Incorrect Data!'),
                    _('Tax Case 91 is only allowed for the declaration of December.'))
            if tax_info[item][1] and item in list_of_tags:
                cases_list.append(item)
        cases_list.sort()
        grid_data_list = []
        for item in cases_list:
            grid_data_list.append({
                'code': str(int(item)),
                'name': tax_info[item][0],
                'amount': '%.2f' % abs(tax_info[item][1]),  # used in xml
                'amt': abs(tax_info[item][1]),  # used in pdf
            })
        xml_dict.update({'grid_data_list': grid_data_list})

        return xml_dict

    def create_xml(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')

        xml_data = self._get_datas(cr, uid, ids, context=context)
        data_of_file = """<?xml version="1.0"?>
<ns2:VATConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/VATConsignment" VATDeclarationsNbr="1">
    <ns2:VATDeclaration SequenceNumber="1" DeclarantReference="%(send_ref)s">
        <ns2:Declarant>
            <VATNumber xmlns="http://www.minfin.fgov.be/InputCommon">%(only_vat)s</VATNumber>
            <Name>%(cmpny_name)s</Name>
            <Street>%(address)s</Street>
            <PostCode>%(post_code)s</PostCode>
            <City>%(city)s</City>
            <CountryCode>%(country_code)s</CountryCode>
            <EmailAddress>%(email)s</EmailAddress>
            <Phone>%(phone)s</Phone>
        </ns2:Declarant>
        <ns2:Period>
    """ % (xml_data)

        starting_month = xml_data['month']
        ending_month = xml_data['ending_month']
        year = xml_data['year']
        quarter = xml_data['quarter']
        if starting_month != ending_month:
            #starting month and ending month of selected period are not the same
            #it means that the accounting isn't based on periods of 1 month but on quarters
            data_of_file += '\t\t<ns2:Quarter>%(quarter)s</ns2:Quarter>\n\t\t' % (xml_data)
        else:
            data_of_file += '\t\t<ns2:Month>%(month)s</ns2:Month>\n\t\t' % (xml_data)
        data_of_file += '\t<ns2:Year>%(year)s</ns2:Year>' % (xml_data)
        data_of_file += '\n\t\t</ns2:Period>\n'

        data_of_file += '\t\t<ns2:Data>\t'
        grid_data_list = xml_data['grid_data_list']
        for grid_data in grid_data_list:
            data_of_file += '\n\t\t\t<ns2:Amount GridNumber="%(code)s">%(amount)s</ns2:Amount''>' % (grid_data)
        data_of_file += '\n\t\t</ns2:Data>'

        data_of_file += '\n\t\t<ns2:ClientListingNihil>%(client_nihil)s</ns2:ClientListingNihil>' % (xml_data)
        data_of_file += '\n\t\t<ns2:Ask Restitution="%(ask_restitution)s" Payment="%(ask_payment)s"/>' % (xml_data)
        if xml_data['comments']:
            data_of_file += '\n\t\t<ns2:Comment>%(comments)s</ns2:Comment>' % (xml_data)
        data_of_file += '\n\t</ns2:VATDeclaration> \n</ns2:VATConsignment>'
        model_data_ids = mod_obj.search(cr, uid, [
            ('model', '=', 'ir.ui.view'), ('name', '=',  'view_vat_save')
            ], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids,
            fields=['res_id'], context=context)[0]['res_id']
        self.write(cr, uid, ids, {
            'file_save': base64.encodestring(data_of_file.encode('utf8')),
            'name': 'vat_declaration_%s_%s.xml'
            % (year, starting_month != ending_month and ('Q' + quarter) or starting_month.ljust(2, '0')),
            }, context=context)

        return {
            'name': _('XML File has been Created'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'res_model': 'l10n_be.vat.declaration',
            'views': [(resource_id, 'form')],
            'view_id': 'view_vat_save',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # add print button
    def print_vat_declaration(self, cr, uid, ids, context=None):
        xml_data = self._get_datas(cr, uid, ids, context=context)
        datas = {
             'ids': [],
             'model': 'l10n_be.vat.declaration',
             'form': xml_data
        }
        return self.pool['report'].get_action(
            cr, uid, [], 'l10n_be_coa_multilang.report_l10nbevatdeclaration',
            data=datas, context=context
        )


class vat_declaration_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(vat_declaration_print, self).__init__(cr, uid, name, context=context)
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        report_date = datetime_field.context_timestamp(self.cr, self.uid,
            datetime.now(), self.context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.localcontext.update({
            'report_date': report_date,
            'period_start': data['form']['period_start'],
            'period_end': data['form']['period_end'],
            'grid_data_list': data['form']['grid_data_list']
        })
        super(vat_declaration_print, self).set_context(objects, data, ids)


class wrapped_vat_declaration_print(orm.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.report_l10nbevatdeclaration'
    _inherit = 'report.abstract_report'
    _template = 'l10n_be_coa_multilang.report_l10nbevatdeclaration'
    _wrapped_report_class = vat_declaration_print
