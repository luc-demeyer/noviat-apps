# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from lxml import etree

from odoo import api, fields, models, _
from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
from odoo.report import report_sxw
from openerp.tools.translate import translate
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

IR_TRANSLATION_NAME = 'l10n.be.vat.listing'


class l10nBeVatListing(models.TransientModel):
    _name = 'l10n.be.vat.listing'
    _inherit = 'l10n.be.vat.common'
    _description = 'Annual Listing of VAT subjected Customers'

    limit_amount = fields.Integer(
        string='Limit Amount',
        required=True,
        default=lambda self: self._default_limit_amount())
    # result view fields
    client_ids = fields.One2many(
        comodel_name='l10n.be.vat.listing.client',
        inverse_name='listing_id',
        string='Clients',
        help="Uncheck the TIN check box of the customer record in order to "
             "remove customers which should not be included in this report.")

    @api.model
    def _default_limit_amount(self):
        return 250

    @api.onchange('year')
    def _onchange_year(self):
        if self.year:
            self.date_from = '%s-01-01' % self.year
            self.date_to = '%s-12-31' % self.year

    @api.multi
    def generate_declaration(self):
        self.ensure_one()
        client_vals = self._get_client_vals()
        self.client_ids = [(0, 0, x) for x in client_vals]

        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.%s_view_form_client_listing' % (module, self._table))

        return {
            'name': _('Annual Listing of VAT subjected Customers'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'target': 'inline',
            'view_id': result_view.id,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def create_xls(self):
        module = __name__.split('addons.')[1].split('.')[0]
        report_name = '%s.report_l10n_be_vat_listing_xlsx' % module
        report = {
            'type': 'ir.actions.report.xml',
            'report_type': 'xlsx',
            'report_name': report_name,
            'context': dict(self.env.context, xlsx_export=True),
            'datas': {'ids': [self.id]},
        }
        return report

    @api.multi
    def create_xml(self):
        """
        Intervat XML Client Listing.
        In the current version of this module the 'Representative'
        is equal to the 'Declarant'.
        """

        ns_map = {
            None: 'http://www.minfin.fgov.be/ClientListingConsignment',
            'ic': 'http://www.minfin.fgov.be/InputCommon',
        }

        Doc = etree.Element(
            'ClientListingConsignment',
            attrib={'ClientListingsNbr': '1'},
            nsmap=ns_map)

        self._node_Representative(Doc, ns_map)
        ref = self._get_declaration_ref()
        self._node_RepresentativeReference(Doc, ns_map, ref)

        self._node_ClientListing(Doc, ns_map, ref)

        xml_string = etree.tostring(
            Doc, pretty_print=True,
            encoding='ISO-8859-1', xml_declaration=True)

        self._validate_xmlschema(xml_string, 'NewLK-in_v0_9.xsd')
        self.file_name = 'vat_list_%s.xml' % self.year
        self.file_save = base64.encodestring(xml_string)

        return self._action_save_xml()

    @api.multi
    def print_declaration(self):
        module = __name__.split('addons.')[1].split('.')[0]
        return self.env['report'].get_action(
            self, '%s.report_l10nbevatlisting' % module)

    def _get_client_vals(self):
        partner_dom = self._get_partner_domain()
        partners = self.env['res.partner'].search(partner_dom)
        if not partners:
            raise UserError(_(
                "No Belgian VAT subjected customers found."))

        flds = ['partner_id', 'debit', 'credit']
        groupby = ['partner_id']

        aml_dom = self._get_move_line_date_domain()
        aml_dom += [('partner_id', 'in', partners.ids)]
        base_dom, vat_dom = self._get_move_line_tax_domains()

        base_data = self.env['account.move.line'].read_group(
            aml_dom + base_dom, flds, groupby)
        vat_dom += [('partner_id', 'in', partners.ids)]
        vat_data = self.env['account.move.line'].read_group(
            aml_dom + vat_dom, flds, groupby)

        partners = partners.filtered(
            lambda r: r.id in [x['partner_id'][0] for x in base_data])
        if not partners:
            raise UserError(_(
                "No VAT subjected transactions found for %s."
                ) % self.year)

        records = {}
        for i, entry in enumerate(base_data):
            vat = self._normalise_vat(partners[i].vat)
            records[entry['partner_id'][0]] = {
                'name': entry['partner_id'][1],
                'vat': vat,
                'base_amount': entry['credit'] - entry['debit'],
            }
        for entry in vat_data:
            records[entry['partner_id'][0]]['vat_amount'] = \
                entry['credit'] - entry['debit']

        # remove entries < limit amount
        client_list = []
        vat_group = {}
        for k in records:
            client = records[k]
            client['partner_id'] = k
            vat = client['vat']
            if vat in vat_group:
                vat_group[vat]['base_total'] += client['base_amount']
                vat_group[vat]['entries'].append(client)
            else:
                vat_group[vat] = {
                    'base_total': client['base_amount'],
                    'entries': [client]}
        for k in vat_group:
            if vat_group[k]['base_total'] >= self.limit_amount:
                client_list += vat_group[k]['entries']

        client_list.sort(key=lambda k: k['vat'])
        return client_list

    def _get_partner_domain(self):
        partner_dom = [
            '|', ('active', '=', True), ('active', '=', False),
            ('vat', '=ilike', 'BE%'),
            ('vat_subjected', '=', True),   # cf. FODFIN Notice 725
        ]
        return partner_dom

    def _get_move_line_tax_domains(self):

        codes_base = ('00', '01', '02', '03', '45')  # base amount codes
        taxes_base = self.env['account.tax'].search(
            [('tag_ids.code', 'in', codes_base)])
        base_dom = [('tax_ids.id', 'in', taxes_base.ids)]

        codes_vat = ('01', '02', '03')  # tax amount codes
        taxes_vat = taxes_base.filtered(
            lambda r:
            any(c in codes_vat for c in r.tag_ids.mapped('code')))
        vat_dom = [('tax_line_id.id', 'in', taxes_vat.ids)]

        return base_dom, vat_dom

    def _get_client_list(self):
        client_list = {}
        for client in self.client_ids:
            vat = client.vat
            if vat in client_list:
                client_list[vat]['base_amount'] += client.base_amount
                client_list[vat]['vat_amount'] += client.vat_amount
            else:
                client_list[vat] = {
                    'base_amount': client.base_amount,
                    'vat_amount': client.vat_amount}
        return client_list

    def _node_ClientListing(self, parent, ns_map, ref):
        client_list = self._get_client_list()
        TurnOverSum = sum([x['base_amount'] for x in client_list.values()])
        VATAmountSum = sum([x['vat_amount'] for x in client_list.values()])

        ClientListing = etree.SubElement(
            parent, 'ClientListing',
            attrib={
                'SequenceNumber': '1',
                'ClientsNbr': '%s' % len(client_list),
                'DeclarantReference': ref,
                'TurnOverSum': '%.2f' % TurnOverSum,
                'VATAmountSum': '%.2f' % VATAmountSum,
            }
        )

        # ReplacedClientListing not supported at this point in time
        # TODO:
        # Create object to save legal VAT declarations in order to
        # and add support of replacements.
        # self._node_ReplacedClientListing(ClientListing, ns_map, replace_ref)

        self._node_Declarant(ClientListing, ns_map)

        Period = etree.SubElement(ClientListing, 'Period')
        Period.text = str(self.year)

        # not supported at this point in time:
        # self._node_TurnOver(ClientListing, ns_map)
        # self._node_Farmer(ClientListing, ns_map)

        seq = 1
        for k in client_list:
            client = {
                'vat': k,
                'base_amount': client_list[k]['base_amount'],
                'vat_amount': client_list[k]['vat_amount']}
            self._node_Client(ClientListing, ns_map, client, seq)
            seq += 1

        # TODO: add support for attachments
        # self._node_FileAttachment(parent, ns_map)

        self._node_Comment(ClientListing, ns_map)

    def _node_Client(self, ClientListing, ns_map, client, seq):
        Client = etree.SubElement(
            ClientListing, 'Client',
            attrib={'SequenceNumber': str(seq)}
        )

        CompanyVATNumber = etree.SubElement(
            Client, 'CompanyVATNumber',
            attrib={'issuedBy': client['vat'][:2]},
        )
        CompanyVATNumber.text = client['vat'][2:]

        TurnOver = etree.SubElement(
            Client, 'TurnOver')
        TurnOver.text = '%.2f' % client['base_amount']

        VATAmount = etree.SubElement(
            Client, 'VATAmount')
        VATAmount.text = '%.2f' % client['vat_amount']


class l10nBeVatListingClient(models.TransientModel):
    _name = 'l10n.be.vat.listing.client'

    listing_id = fields.Many2one(
        comodel_name='l10n.be.vat.listing',
        string='Client Listing')
    partner_id = fields.Many2one(
        comodel_name='res.partner', readonly=1)
    vat = fields.Char(
        string='VAT Number', readonly=1)
    base_amount = fields.Monetary(
        string='Base Amount', currency_field='currency_id',
        readonly=1)
    vat_amount = fields.Monetary(
        string='VAT Amount', currency_field='currency_id',
        readonly=1)
    currency_id = fields.Many2one(
        related='listing_id.currency_id',
        readonly=1)

    @api.multi
    def view_move_lines(self):
        self.ensure_one()
        act_window = self.listing_id._move_lines_act_window()
        aml_dom = self.listing_id._get_move_line_date_domain()
        aml_dom += [('partner_id', '=', self.partner_id.id)]
        base_dom, vat_dom = self.listing_id._get_move_line_tax_domains()
        aml_dom += ['|'] + base_dom + vat_dom
        act_window['domain'] = aml_dom
        return act_window


class l10nBeVatListingXlsx(AbstractReportXlsx):

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, workbook, data, listing):

        col_specs = {
            'seq': {
                'header': {
                    'value': self._('Nr'),
                },
                'lines': {
                    'value': self._render("str(seq)"),
                },
                'width': 5,
            },
            'vat': {
                'header': {
                    'value': self._('VAT Number'),
                },
                'lines': {
                    'value': self._render("c.vat"),
                },
                'width': 18,
            },
            'partner': {
                'header': {
                    'value': self._('Partner'),
                },
                'lines': {
                    'value': self._render("c.partner_id.name"),
                },
                'width': 52,
            },
            'base_amount': {
                'header': {
                    'value': self._('Base Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("c.base_amount"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("total_base_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'vat_amount': {
                'header': {
                    'value': self._('VAT Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("c.vat_amount"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("total_vat_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
        }
        wanted_list = ['seq', 'vat', 'partner', 'base_amount', 'vat_amount']

        return [{
            'ws_name': 'vat_list_%s' % listing.year,
            'generate_ws_method': '_generate_listing',
            'title': listing._description,
            'wanted_list': wanted_list,
            'col_specs': col_specs,
        }]

    def _generate_listing(self, workbook, ws, ws_params, data, listing):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._listing_title(ws, row_pos, ws_params, data, listing)
        row_pos = self._listing_info(ws, row_pos, ws_params, data, listing)
        row_pos = self._listing_lines(ws, row_pos, ws_params, data, listing)

    def _listing_title(self, ws, row_pos, ws_params, data, listing):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _listing_info(self, ws, row_pos, ws_params, data, listing):
        ws.write_string(row_pos, 1, self._('Company') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, listing.company_id.name)
        row_pos += 1
        ws.write_string(row_pos, 1, self._('VAT Number') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, listing.company_id.vat)
        row_pos += 1
        ws.write_string(row_pos, 1, self._('Year') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, listing.year)
        return row_pos + 2

    def _listing_lines(self, ws, row_pos, ws_params, data, listing):

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        seq = 1
        row_pos_start = row_pos
        previous_client = False
        for c in listing.client_ids:
            if seq > 1:
                if c.vat == previous_client.vat:
                    seq -= 1
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={'seq': seq, 'c': c},
                default_format=self.format_tcell_left)
            seq += 1
            previous_client = c

        base_pos = ws_params['wanted_list'].index('base_amount')
        base_start = self._rowcol_to_cell(row_pos_start, base_pos)
        base_stop = self._rowcol_to_cell(row_pos - 1, base_pos)
        total_base_formula = 'SUM(%s:%s)' % (base_start, base_stop)
        vat_pos = ws_params['wanted_list'].index('vat_amount')
        vat_start = self._rowcol_to_cell(row_pos_start, vat_pos)
        vat_stop = self._rowcol_to_cell(row_pos - 1, vat_pos)
        total_vat_formula = 'SUM(%s:%s)' % (vat_start, vat_stop)
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'total_base_formula': total_base_formula,
                'total_vat_formula': total_vat_formula,
            },
            default_format=self.format_theader_yellow_left)

        return row_pos + 1


l10nBeVatListingXlsx(
    'report.l10n_be_coa_multilang.report_l10n_be_vat_listing_xlsx',
    'l10n.be.vat.listing',
    parser=report_sxw.rml_parse)
