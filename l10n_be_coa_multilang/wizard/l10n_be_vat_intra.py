# -*- coding: utf-8 -*-
# noqa: skip pep8 control until this wizard is rewritten.
# flake8: noqa
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Corrections & modifications by Noviat nv/sa, (http://www.noviat.com):
#     - support Noviat tax code scheme
#     - align with periodical VAT declaration
#     - grouping by vat number / code
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

import time
import base64
import operator
from datetime import datetime
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.report import report_sxw
import logging
_logger = logging.getLogger(__name__)


class partner_vat_intra(orm.TransientModel):
    """ VAT Intracom declaration
    """
    _name = 'partner.vat.intra'
    _description = 'Partner VAT Intra'

    def _get_period(self, cr, uid, context=None):
        domain = [('special', '=', False), ('date_stop', '<', time.strftime('%Y-%m-%d'))]
        result = self.pool.get('account.period').search(cr, uid, domain)
        return result and result[-1:] or False

    def _get_europe_country(self, cr, uid, context=None):
        return self.pool.get('res.country').search(cr, uid, [('code', 'in',
            ['AT', 'BG', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR',
             'HR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL',
             'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB'])])

    def _get_tax_code(self, cr, uid, context=None):
        obj_tax_code = self.pool.get('account.tax.code')
        obj_user = self.pool.get('res.users')
        company_id = obj_user.browse(cr, uid, uid, context=context).company_id.id
        tax_code_ids = obj_tax_code.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', False)], context=context)
        return tax_code_ids and tax_code_ids[0] or False

    _columns = {
        'name': fields.char('File Name', size=32),
        'file_save': fields.binary('Save File', readonly=True),
        'period_ids': fields.many2many('account.period', 'vat_intra_period_rel', 'acc_id', 'period_id', 'Period (s)', required=True,
            help='Select here the period(s) you want to include in your Intracom declaration'),
        'period_code': fields.char('Period Code', size=6, required=True,
            help="""This field allows you to override the period code for the Intracom declaration.
      Format: PPYYYY
      PP can stand for a month: from '01' to '12'.
      PP can stand for a trimester: '31','32','33','34'
          The first figure means that it is a trimester,
          The second figure identify the trimester.
      PP can stand for a complete fiscal year: '00'.
      YYYY stands for the year (4 positions).
    """
        ),

        'tax_code_id': fields.many2one('account.tax.code', 'Company', domain=[('parent_id', '=', False)], help="Keep empty to use the user's company", required=True),
        'country_ids': fields.many2many('res.country', 'vat_country_rel', 'vat_id', 'country_id', 'European Countries'),
        'comments': fields.text('Comments'),
        }

    _defaults = {
        'period_ids': _get_period,
        'country_ids': _get_europe_country,
        'tax_code_id': _get_tax_code,
    }

    def _get_datas(self, cr, uid, ids, context=None):
        """Collects required data for vat intra xml
        :param ids: id of wizard.
        :return: dict of all data to be used to generate xml for Partner VAT Intra.
        :rtype: dict
        """
        if context is None:
            context = {}

        obj_user = self.pool.get('res.users')
        obj_sequence = self.pool.get('ir.sequence')
        obj_partner = self.pool.get('res.partner')

        xmldict = {}
        post_code = street = city = country = data_clientinfo = ''
        seq = amount_sum = 0

        wiz_data = self.browse(cr, uid, ids[0], context=context)
        comments = wiz_data.comments

        if wiz_data.tax_code_id:
            data_company = wiz_data.tax_code_id.company_id
        else:
            data_company = obj_user.browse(cr, uid, uid, context=context).company_id

        # Get Company vat
        company_vat = data_company.partner_id.vat
        if not company_vat:
            raise orm.except_orm(_('insufficient data!'), _('No VAT number associated with your company.'))
        company_vat = company_vat.replace(' ', '').upper()
        issued_by = company_vat[:2]

        if wiz_data.period_code and len(wiz_data.period_code) != 6:
            raise orm.except_orm(_('Error!'), _('Period code is not valid.'))

        if not wiz_data.period_ids:
            raise orm.except_orm(_('Insufficient Data!'), _('Please select at least one Period.'))

        p_id_list = obj_partner.search(cr, uid, [('vat', '!=', False)], context=context)
        if not p_id_list:
            raise orm.except_orm(_('Insufficient Data!'), _('No partner has a VAT number asociated with him.'))

        seq_declarantnum = obj_sequence.get(cr, uid, 'declarantseq')
        dnum = company_vat[2:] + seq_declarantnum[-4:]

        addr = obj_partner.address_get(cr, uid, [data_company.partner_id.id], ['invoice'])
        email = data_company.partner_id.email or ''
        phone = data_company.partner_id.phone or ''

        if addr.get('invoice', False):
            ads = obj_partner.browse(cr, uid, [addr['invoice']])[0]
            city = (ads.city or '')
            post_code = (ads.zip or '')
            if ads.street:
                street = ads.street
            if ads.street2:
                street += ' '
                street += ads.street2
            if ads.country_id:
                country = ads.country_id.code

        if not country:
            country = company_vat[:2]
        if not email:
            raise orm.except_orm(_('Insufficient Data!'), _('No email address associated with the company.'))
        if not phone:
            raise orm.except_orm(_('Insufficient Data!'), _('No phone associated with the company.'))

        account_periods = wiz_data.period_ids

        period_end_dates = sorted([x.date_stop for x in account_periods])
        period_start_dates = sorted([x.date_start for x in account_periods])

        starting_month = period_start_dates[0][5:7]
        ending_month = period_end_dates[-1][5:7]
        year = period_end_dates[-1][:4]
        quarter = str(((int(starting_month) - 1) / 3) + 1)

        xmldict.update({
            'company_name': data_company.name,
            'company_vat': company_vat,
            'vatnum':  company_vat[2:],
            #'mand_id': wiz_data.mand_id, # dropped since also not supported in periodical VAT declaration
            'sender_date': str(time.strftime('%Y-%m-%d')),
            'street': street,
            'city': city,
            'post_code': post_code,
            'country': country,
            'email': email,
            'phone': phone.replace('/', '').replace('.', '').replace('(', '').replace(')', '').replace(' ', ''),
            'period_code': wiz_data.period_code,
            'quarter': quarter,
            'starting_month': starting_month,
            'ending_month': ending_month,
            'year': year,
            'clientlist': [],
            'comments': comments,
            'issued_by': issued_by,
            })

        codes = ('44', '46L', '46T', '48s44', '48s46L', '48s46T')
        cr.execute(
            """
            SELECT COALESCE(REPLACE(p.vat, ' ',''),'') AS vat,
              (CASE WHEN t.code IN ('44', '48s44') THEN 'S'
                    WHEN t.code IN ('46L', '48s46L') THEN 'L'
                    WHEN t.code IN ('46T', '48s46T') THEN 'T'
                    ELSE t.code END) AS intra_code,
              p.name AS partner_name, l.partner_id AS partner_id,
              SUM(CASE WHEN t.code IN ('48s44','48s46L','48s46T') 
                       THEN -l.tax_amount 
                       ELSE l.tax_amount END) AS amount
              FROM account_move_line l
                INNER JOIN account_tax_code t ON (l.tax_code_id = t.id)
                LEFT JOIN res_partner p ON (l.partner_id = p.id)
                WHERE t.code IN %s
                  AND l.period_id IN %s
                  AND t.company_id = %s
                  AND (l.debit + l.credit) != 0
                GROUP BY vat, intra_code, partner_name, partner_id
                ORDER BY vat, intra_code, partner_name, partner_id
            """,
            (codes, tuple([p.id for p in wiz_data.period_ids]), data_company.id))
        records = cr.dictfetchall()
        if not records:
            raise orm.except_orm(
                _('No Data Available'),
                _('No intracom transactions found for the selected period(s) !'))

        p_count = 0
        previous_vat = previous_code = False
        for record in records:
            if not record['vat']:
                p_count += 1
            if record['vat'] != previous_vat or record['intra_code'] != previous_code:
                seq += 1
            previous_vat = record['vat']
            previous_code = record['intra_code']
            amt = record['amount'] or 0.0
            amount_sum += amt
            xmldict['clientlist'].append({
                'partner_name': record['partner_name'],
                'seq': seq,
                'vatnum': record['vat'][2:],
                'vat': record['vat'],
                'country': record['vat'][:2],
                'amount': '%.2f' % amt,  # used in xml
                'amt': amt,  # used in pdf
                'intra_code': record['intra_code'],
            })

        xmldict.update({
            'dnum': dnum,
            'clientnbr': str(seq),
            'amountsum': '%.2f' % amount_sum,  # used in xml
            'amtsum': amount_sum,  # used in pdf
            'partner_wo_vat': p_count})
        return xmldict

    def create_xml(self, cr, uid, ids, context=None):
        """Creates xml that is to be exported and sent to estate for partner vat intra.
        :return: Value for next action.
        :rtype: dict
        """
        mod_obj = self.pool.get('ir.model.data')
        xml_data = self._get_datas(cr, uid, ids, context=context)
        data_file = ''

        # TODO: change code to use etree + add schema verification
        data_head = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ns2:IntraConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/IntraConsignment" IntraListingsNbr="1">
        """
        data_comp_period = '\n\t\t<ns2:Declarant>' \
            '\n\t\t\t<VATNumber>%(vatnum)s</VATNumber>' \
            '\n\t\t\t<Name>%(company_name)s</Name>' \
            '\n\t\t\t<Street>%(street)s</Street>' \
            '\n\t\t\t<PostCode>%(post_code)s</PostCode>' \
            '\n\t\t\t<City>%(city)s</City>' \
            '\n\t\t\t<CountryCode>%(country)s</CountryCode>' \
            '\n\t\t\t<EmailAddress>%(email)s</EmailAddress>' \
            '\n\t\t\t<Phone>%(phone)s</Phone>' \
            '\n\t\t</ns2:Declarant>' \
            % (xml_data)

        if xml_data['period_code']:
            month_quarter = xml_data['period_code'][:2]
            year = xml_data['period_code'][2:]
            if month_quarter.startswith('3'):
                data_comp_period += '\n\t\t<ns2:Period>\n\t\t\t<ns2:Quarter>' + month_quarter[1] + \
                    '</ns2:Quarter> \n\t\t\t<ns2:Year>' + year + \
                    '</ns2:Year>\n\t\t</ns2:Period>'
            elif month_quarter.startswith('0') and month_quarter.endswith('0'):
                data_comp_period += '\n\t\t<ns2:Period>\n\t\t\t<ns2:Year>' + year + \
                    '</ns2:Year>\n\t\t</ns2:Period>'
            else:
                data_comp_period += '\n\t\t<ns2:Period>\n\t\t\t<ns2:Month>' + month_quarter + \
                    '</ns2:Month> \n\t\t\t<ns2:Year>' + year + \
                    '</ns2:Year>\n\t\t</ns2:Period>'
        else:
            year = xml_data['year']
            if xml_data['starting_month'] != xml_data['ending_month']:
                month_quarter = '3' + xml_data['quarter']
                #starting month and ending month of selected period are not the same
                #it means that the accounting is not based on periods of 1 month but on quarters
                data_comp_period += '\n\t\t<ns2:Period>\n\t\t\t<ns2:Quarter>%(quarter)s</ns2:Quarter> \n\t\t\t<ns2:Year>%(year)s</ns2:Year>\n\t\t</ns2:Period>' % (xml_data)
            else:
                month_quarter = xml_data['ending_month']
                data_comp_period += '\n\t\t<ns2:Period>\n\t\t\t<ns2:Month>' + xml_data['ending_month'] + \
                    '</ns2:Month> \n\t\t\t<ns2:Year>%(year)s</ns2:Year>\n\t\t</ns2:Period>' \
                    % (xml_data)

        records = xml_data['clientlist']
        client_datas = []
        previous_record = {}
        for record in records:
            if record['vat'] == previous_record.get('vat') \
                    and record['intra_code'] == previous_record.get('intra_code'):
                client_datas.pop()
                record['amt'] += previous_record['amt']
                record['amount'] = '%.2f' % record['amt']
                record['partner_name'] += ', ' + previous_record['partner_name']
            client_datas.append(record)
            previous_record = record

        data_clientinfo = ''
        for client_data in client_datas:
            if not client_data['vatnum']:
                raise orm.except_orm(
                    _('Insufficient Data!'),
                    _('No vat number defined for %s.')
                    % client_data['partner_name'])
            data_clientinfo += '\n\t\t<ns2:IntraClient SequenceNumber="%(seq)s">' \
                '\n\t\t\t<ns2:CompanyVATNumber issuedBy="%(country)s">%(vatnum)s</ns2:CompanyVATNumber>' \
                '\n\t\t\t<ns2:Code>%(intra_code)s</ns2:Code>' \
                '\n\t\t\t<ns2:Amount>%(amount)s</ns2:Amount>' \
                '\n\t\t</ns2:IntraClient>' \
                % (client_data)

        data_decl = '\n\t<ns2:IntraListing SequenceNumber="1" ClientsNbr="%(clientnbr)s" DeclarantReference="%(dnum)s" AmountSum="%(amountsum)s">' % (xml_data)

        data_file += data_head + data_decl + data_comp_period + data_clientinfo
        if xml_data['comments']:
            data_file += '\n\t\t<ns2:Comment>%(comments)s</ns2:Comment>' % (xml_data)
        data_file += '\n\t</ns2:IntraListing>\n</ns2:IntraConsignment>'

        self.write(cr, uid, ids, {
            'file_save': base64.encodestring(data_file.encode('utf8')),
            'name': 'vat_intra_%s_%s.xml' % (year, month_quarter[0] == '3' and ('Q' + month_quarter[1]) or month_quarter),
            }, context=context)

        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_vat_intra_save')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _('Save'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'res_model': 'partner.vat.intra',
            'views': [(resource_id, 'form')],
            'view_id': 'view_vat_intra_save',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def print_vatintra(self, cr, uid, ids, context=None):
        xml_data = self._get_datas(cr, uid, ids, context=context)
        datas = {
             'ids': [],
             'model': 'partner.vat.intra',
             'form': xml_data
        }
        return self.pool['report'].get_action(
            cr, uid, [], 'l10n_be_coa_multilang.report_l10nbevatintra',
            data=datas, context=context
        )


class vat_intra_print(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(vat_intra_print, self).__init__(cr, uid, name, context=context)
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        report_date = datetime_field.context_timestamp(self.cr, self.uid,
            datetime.now(), self.context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.localcontext.update({
            'period_code': data['form']['period_code'],
            'partner_wo_vat': data['form']['partner_wo_vat'],
            'amtsum': data['form']['amtsum'],
            'report_date': report_date,
            'clientlist': data['form']['clientlist'],
        })
        super(vat_intra_print, self).set_context(objects, data, ids)


class wrapped_vat_intra_print(orm.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.report_l10nbevatintra'
    _inherit = 'report.abstract_report'
    _template = 'l10n_be_coa_multilang.report_l10nbevatintra'
    _wrapped_report_class = vat_intra_print

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
