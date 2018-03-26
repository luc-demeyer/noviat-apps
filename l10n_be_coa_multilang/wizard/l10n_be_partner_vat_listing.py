# -*- coding: utf-8 -*-
# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
import base64
from datetime import datetime

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
from openerp.osv.fields import datetime as datetime_field
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.report import report_sxw
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class VatListingClients(models.TransientModel):
    _name = 'vat.listing.clients'

    name = fields.Char(string='Client Name')
    vat = fields.Char(string='VAT')
    turnover = fields.Float(
        string='Base Amount', digits=dp.get_precision('Account'))
    vat_amount = fields.Float(
        string='VAT Amount', digits=dp.get_precision('Account'))


class PartnerVat(models.TransientModel):
    _name = 'partner.vat'

    year = fields.Char(
        string='Year', size=4, required=True,
        default=str(int(time.strftime('%Y')) - 1))
    limit_amount = fields.Integer(
        string='Limit Amount', required=True, default=250)

    def get_partner(self, cr, uid, ids, context=None):
        obj_period = self.pool['account.period']
        obj_partner = self.pool['res.partner']
        obj_vat_lclient = self.pool['vat.listing.clients']
        obj_model_data = self.pool['ir.model.data']
        data = self.read(cr, uid, ids)[0]
        year = data['year']
        date_start = year + '-01-01'
        date_stop = year + '-12-31'
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(
                cr, uid, uid, context=context).company_id.id
        period_ids = obj_period.search(
            cr, uid,
            [('date_start', '>=', date_start),
             ('date_stop', '<=', date_stop), ('company_id', '=', company_id)])
        if not period_ids:
            raise UserError(
                _('Insufficient Data!') + '\n' +
                _('No data for the selected year.'))

        partners = []
        # FODFIN Notice 725:
        # All customers with Belgian VAT number must be included in the annual
        # VAT Listing, except those with only operations according article 44
        # of the VAT lawbook (reported via tax code 00).
        # You should uncheck the 'vat_subjected' flag for those customers.
        partner_dom = [
            '|', ('active', '=', True), ('active', '=', False),
            ('vat', '=ilike', 'BE%'),
            ('vat_subjected', '=', True),
        ]
        partner_ids = obj_partner.search(
            cr, uid, partner_dom, context=context)
        if not partner_ids:
            raise UserError(
                _('Error') + '\n' +
                _('No belgian customers with a VAT number in your database.'))
        codes = ('00', '01', '02', '03', '45', '49')
        cr.execute("""
    SELECT sub1.partner_id, sub1.name, sub1.vat,
           COALESCE(sub1.turnover, 0.0) AS turnover,
           COALESCE(sub2.vat_amount, 0.0) AS vat_amount
    FROM
      (SELECT l.partner_id, p.name, COALESCE(p.vat,'') AS vat,
       SUM(CASE WHEN c.code ='49' THEN -l.tax_amount ELSE l.tax_amount END
           ) AS turnover
       FROM account_move_line l
       LEFT JOIN res_partner p ON l.partner_id = p.id
       LEFT JOIN account_tax_code c ON l.tax_code_id = c.id
       WHERE c.code IN %s
         AND l.partner_id IN %s
         AND l.period_id IN %s
       GROUP BY l.partner_id, p.name, p.vat) AS sub1
      LEFT JOIN
        (SELECT l2.partner_id,
         SUM(CASE WHEN c2.code ='64' THEN -l2.tax_amount
             ELSE l2.tax_amount END) AS vat_amount
         FROM account_move_line l2
         LEFT JOIN account_tax_code c2 ON l2.tax_code_id = c2.id
         WHERE c2.code IN ('54','64')
         AND l2.partner_id IN %s
         AND l2.period_id IN %s
        GROUP BY l2.partner_id) AS sub2
        ON sub1.partner_id = sub2.partner_id
            """, (codes, tuple(partner_ids), tuple(period_ids),
                  tuple(partner_ids), tuple(period_ids))
        )

        client_list = []
        vat_group = {}
        # remove entries < limit amount
        for client in cr.dictfetchall():
            vat = client['vat'].replace(' ', '').replace('.', '').upper()
            client['vat'] = vat
            if vat in vat_group:
                vat_group[vat]['turnover'] += client['turnover']
                vat_group[vat]['entries'].append(client)
            else:
                vat_group[vat] = {
                    'turnover': client['turnover'],
                    'entries': [client]}
        for k in vat_group:
            if vat_group[k]['turnover'] >= data['limit_amount']:
                client_list += vat_group[k]['entries']

        client_list.sort(key=lambda k: k['vat'])
        curr = self.pool['res.company'].browse(
            cr, uid, company_id).currency_id
        for client in client_list:
            del client['partner_id']
            if curr.is_zero(client['turnover']) \
                    and curr.is_zero(client['vat_amount']):
                continue
            id_client = obj_vat_lclient.create(
                cr, uid, client, context=context)
            partners.append(id_client)

        if not partners:
            raise UserError(
                _('insufficient data!') + '\n' +
                _('No data found for the selected year.'))
        context.update({
            'partner_ids': partners,
            'year': data['year'],
            'limit_amount': data['limit_amount']
        })
        model_data_ids = obj_model_data.search(
            cr, uid,
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'view_vat_listing')])
        resource_id = obj_model_data.read(
            cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'name': _('Vat Listing'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.vat.list',
            'views': [(resource_id, 'form')],
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class PartnerVatList(models.TransientModel):
    _name = 'partner.vat.list'

    partner_ids = fields.Many2many(
        comodel_name='vat.listing.clients',
        relation='vat_partner_rel',
        column1='vat_id', column2='partner_id',
        string='Clients',
        default=lambda self: self._default_partner_ids(),
        help="Uncheck the TIN check box of the customer record in order to "
             "remove customers which should not be included in this report.")
    name = fields.Char(string='File Name')
    file_save = fields.Binary(
        string='Save File', readonly=True)
    comments = fields.Text(string='Comments')

    @api.model
    def _default_partner_ids(self):
        return self._context.get('partner_ids', [])

    def _get_datas(self, cr, uid, ids, context=None):
        obj_vat_lclient = self.pool.get('vat.listing.clients')
        datas = []
        data = self.read(cr, uid, ids)[0]
        for partner in data['partner_ids']:
            if isinstance(partner, list) and partner:
                datas.append(partner[2])
            else:
                client_data = obj_vat_lclient.read(
                    cr, uid, partner, context=context)
                datas.append(client_data)
        client_datas = []
        seq = 0
        sum_tax = 0.00
        sum_turnover = 0.00
        amount_data = {}
        previous_vat = False
        for line in datas:
            if not line:
                continue
            if line['vat'] != previous_vat:
                seq += 1
            sum_tax += line['vat_amount']
            sum_turnover += line['turnover']
            vat = line['vat'].replace(' ', '').replace('.', '').upper()
            amount_data = {
                'seq': str(seq),
                'vat': vat,
                'only_vat': vat[2:],
                'turnover': line['turnover'],
                'vat_amount': line['vat_amount'],
                'sum_tax': sum_tax,
                'sum_turnover': sum_turnover,
                'partner_name': line['name'],
            }
            client_datas += [amount_data]
            previous_vat = line['vat']
        return client_datas

    def create_xml(self, cr, uid, ids, context=None):

        obj_sequence = self.pool.get('ir.sequence')
        obj_users = self.pool.get('res.users')
        obj_partner = self.pool.get('res.partner')
        obj_model_data = self.pool.get('ir.model.data')
        obj_cmpny = obj_users.browse(cr, uid, uid, context=context).company_id
        company_vat = obj_cmpny.partner_id.vat
        year = context['year']

        if not company_vat:
            raise UserError(
                _('Insufficient Data!') + '\n' +
                _('No VAT number associated with the company.'))

        company_vat = company_vat.replace(' ', '').replace('.', '').upper()
        SenderId = company_vat[2:]
        issued_by = company_vat[:2]
        seq_declarantnum = obj_sequence.get(cr, uid, 'declarantseq')
        dnum = company_vat[2:] + seq_declarantnum[-4:]
        street = city = country = ''
        addr = obj_partner.address_get(
            cr, uid, [obj_cmpny.partner_id.id], ['invoice'])
        if addr.get('invoice', False):
            ads = obj_partner.browse(
                cr, uid, [addr['invoice']], context=context)[0]
            phone = ads.phone and ads.phone.replace(' ', '') or ''
            email = ads.email or ''
            city = ads.city or ''
            zip = obj_partner.browse(
                cr, uid, ads.id, context=context).zip or ''
            if not city:
                city = ''
            if ads.street:
                street = ads.street
            if ads.street2:
                street += ' ' + ads.street2
            if ads.country_id:
                country = ads.country_id.code

        data = self.read(cr, uid, ids)[0]
        comp_name = obj_cmpny.name

        if not email:
            raise UserError(
                _('Insufficient Data!') + '\n' +
                _('No email address associated with the company.'))
        if not phone:
            raise UserError(
                _('Insufficient Data!') + '\n' +
                _('No phone associated with the company.'))
        annual_listing_data = {
            'issued_by': issued_by,
            'company_vat': company_vat,
            'comp_name': comp_name,
            'street': street,
            'zip': zip,
            'city': city,
            'country': country,
            'email': email,
            'phone': phone,
            'SenderId': SenderId,
            'period': year,
            'comments': data['comments'] or ''
        }

        data_file = '<?xml version="1.0" encoding="ISO-8859-1"?>'
        data_file += """
<ns2:ClientListingConsignment
     xmlns="http://www.minfin.fgov.be/InputCommon"
     xmlns:ns2="http://www.minfin.fgov.be/ClientListingConsignment"
     ClientListingsNbr="1">
        """
        data_comp = """
    <ns2:Declarant>
      <VATNumber>%(SenderId)s</VATNumber>
      <Name>%(comp_name)s</Name>
      <Street>%(street)s</Street>
      <PostCode>%(zip)s</PostCode>
      <City>%(city)s</City>
      <CountryCode>%(country)s</CountryCode>
      <EmailAddress>%(email)s</EmailAddress>
      <Phone>%(phone)s</Phone>
    </ns2:Declarant>
    <ns2:Period>%(period)s</ns2:Period>
        """ % annual_listing_data

        # Turnover and Farmer tags are not included
        records = self._get_datas(cr, uid, ids, context=context)
        if not records:
            raise UserError(
                _('No data!') + '\n' +
                _('No VAT listing data available.'))
        client_datas = []
        previous_record = {}
        for record in records:
            amount_data = record.copy()
            if record['vat'] == previous_record.get('vat'):
                client_datas.pop()
                record['turnover'] += previous_record['turnover']
                record['vat_amount'] += previous_record['vat_amount']
                amount_data['turnover'] += previous_record['turnover']
                amount_data['vat_amount'] += previous_record['vat_amount']
                amount_data['partner_name'] += ', ' + \
                    previous_record['partner_name']
            client_datas.append(amount_data)
            previous_record = record

        data_client_info = ''
        for amount_data in client_datas:
            amount_data.update({
                'turnover': '%.2f' % amount_data['turnover'],
                'vat_amount': '%.2f' % amount_data['vat_amount'],
            })
            data_client_info += """
    <ns2:Client SequenceNumber="%(seq)s">
        <ns2:CompanyVATNumber issuedBy="BE">%(only_vat)s</ns2:CompanyVATNumber>
        <ns2:TurnOver>%(turnover)s</ns2:TurnOver>
        <ns2:VATAmount>%(vat_amount)s</ns2:VATAmount>
    </ns2:Client>""" % amount_data

        amount_data_begin = client_datas[-1]
        amount_data_begin.update({
            'dnum': dnum,
            'sum_turnover': '%.2f' % amount_data_begin['sum_turnover'],
            'sum_tax': '%.2f' % amount_data_begin['sum_tax'],
        })
        data_begin = """
  <ns2:ClientListing SequenceNumber="1" ClientsNbr="%(seq)s"
    DeclarantReference="%(dnum)s"
    TurnOverSum="%(sum_turnover)s" VATAmountSum="%(sum_tax)s">
        """ % amount_data_begin

        data_end = """

    <ns2:Comment>%(comments)s</ns2:Comment>
  </ns2:ClientListing>
</ns2:ClientListingConsignment>
        """ % annual_listing_data

        data_file += data_begin + data_comp + data_client_info + data_end
        file_save = base64.encodestring(data_file.encode('utf8'))
        self.write(
            cr, uid, ids,
            {'file_save': file_save,
             'name': 'vat_list_%s.xml' % year},
            context=context)
        model_data_ids = obj_model_data.search(
            cr, uid,
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'view_vat_listing_result')])
        resource_id = obj_model_data.read(
            cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']

        return {
            'name': _('XML File has been Created'),
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.vat.list',
            'views': [(resource_id, 'form')],
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def print_vatlist(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': []}
        datas['model'] = 'res.company'
        datas['year'] = context['year']
        datas['limit_amount'] = context['limit_amount']
        client_datas = self._get_datas(cr, uid, ids, context=context)
        datas['client_datas'] = client_datas
        if not datas['client_datas']:
            raise UserError(
                _('Error!') + '\n' +
                _('No record to print.'))
        return self.pool['report'].get_action(
            cr, uid, [], 'l10n_be_coa_multilang.report_l10nbevatlisting',
            data=datas, context=context
        )


class PartnerVatListingPrint(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(PartnerVatListingPrint, self).__init__(
            cr, uid, name, context=context)
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        client_datas = data['client_datas']
        report_date = datetime_field.context_timestamp(
            self.cr, self.uid, datetime.now(), self.context
        ).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.localcontext.update({
            'year': data['year'],
            'sum_turnover': client_datas[-1]['sum_turnover'],
            'sum_tax': client_datas[-1]['sum_tax'],
            'client_list': client_datas,
            'report_date': report_date,
        })
        super(PartnerVatListingPrint, self).set_context(
            objects, data, ids)


class WrappedVatListingPrint(models.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.report_l10nbevatlisting'
    _inherit = 'report.abstract_report'
    _template = 'l10n_be_coa_multilang.report_l10nbevatlisting'
    _wrapped_report_class = PartnerVatListingPrint
