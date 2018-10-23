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

IR_TRANSLATION_NAME = 'l10n.be.vat.declaration'


class l10nBeVatDeclaration(models.TransientModel):
    _name = 'l10n.be.vat.declaration'
    _inherit = 'l10n.be.vat.common'
    _description = 'Periodical VAT Declaration'

    ask_restitution = fields.Boolean(
        string='Ask Restitution',
        help='Request for refund')
    ask_payment = fields.Boolean(
        string='Ask Payment',
        help='Request for payment forms')
    client_nihil = fields.Boolean(
        string='Last Declaration, no clients in client listing',
        help='Applies only to the last declaration of the calendar year '
             'or the declaration concerning the cessation of activity:\n'
             'no clients to be included in the client listing.')
    # result view fields
    case_ids = fields.One2many(
        comodel_name='l10n.be.vat.declaration.case',
        inverse_name='declaration_id',
        string='Cases')

    @api.multi
    def generate_declaration(self):
        self.ensure_one()
        self.note = ''
        case_vals = self._get_case_vals()
        self.case_ids = [(0, 0, x) for x in case_vals]

        negative_cases = self.case_ids.filtered(lambda x: x.amount < 0.0)
        warnings = filter(
            lambda x: x.case_id.code in self._intervat_cases(),
            negative_cases)
        if warnings:
            self.note += _(
                "Negative values found for cases %s"
                % [str(x.case_id.code) for x in warnings])
            self.note += '\n'
            self.note += _(
                "These needs to be corrected before submitting the "
                "VAT declaration.")

        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.%s_view_form_declaration' % (module, self._table))

        return {
            'name': _('Periodical VAT Declaration'),
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
        report_name = '%s.report_l10n_be_vat_declaration_xlsx' % module
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
        Intervat XML Periodical VAT Declaration.
        In the current version of this module the 'Representative'
        is equal to the 'Declarant'.
        """

        ns_map = {
            None: 'http://www.minfin.fgov.be/VATConsignment',
            'ic': 'http://www.minfin.fgov.be/InputCommon',
        }

        Doc = etree.Element(
            'VATConsignment',
            attrib={'VATDeclarationsNbr': '1'},
            nsmap=ns_map)

        self._node_Representative(Doc, ns_map)
        ref = self._get_declaration_ref()
        self._node_RepresentativeReference(Doc, ns_map, ref)

        self._node_VATDeclaration(Doc, ns_map, ref)

        xml_string = etree.tostring(
            Doc, pretty_print=True,
            encoding='ISO-8859-1', xml_declaration=True)

        self._validate_xmlschema(xml_string, 'NewTVA-in_v0_9.xsd')
        self.file_name = 'vat_declaration_%s.xml' % self.period
        self.file_save = base64.encodestring(xml_string)

        return self._action_save_xml()

    @api.multi
    def print_declaration(self):
        module = __name__.split('addons.')[1].split('.')[0]
        return self.env['report'].get_action(
            self, '%s.report_l10nbevatdeclaration' % module)

    def _intervat_cases(self):
        return [
            '00', '01', '02', '03', '44', '45', '46', '47', '48', '49',
            '54', '55', '56', '57', '59', '61', '62', '63', '64', '71',
            '72', '81', '82', '83', '84', '85', '86', '87', '88', '91',
        ]

    def _base_out_invoice_cases(self):
        return ['00', '01', '02', '03', '44', '45', '46L', '46T', '47']

    def _base_out_refund_cases(self):
        return ['48', '49']

    def _base_in_invoice_cases(self):
        return []

    def _base_in_refund_cases(self):
        return ['84', '85D']

    def _base_in_invoice_refund_cases(self):
        return ['81D', '82D', '83D', '86', '87', '88']

    def _invoice_base_cases(self):
        cases = (
            self._base_out_invoice_cases() +
            self._base_out_refund_cases() +
            self._base_in_invoice_cases() +
            self._base_in_refund_cases() +
            self._base_in_invoice_refund_cases()
        )
        return cases

    def _tax_debt_out_invoice_cases(self):
        return ['54']

    def _tax_deductible_out_refund_cases(self):
        return ['64']

    def _tax_debt_in_invoice_cases(self):
        return ['55', '56', '57']

    def _tax_deductible_in_invoice_cases(self):
        return ['59', '81ND', '82ND', '83ND']

    def _tax_debt_in_refund_cases(self):
        return ['63', '85ND']

    def _invoice_tax_cases(self):
        cases = (
            self._tax_debt_out_invoice_cases() +
            self._tax_deductible_out_refund_cases() +
            self._tax_debt_in_invoice_cases() +
            self._tax_deductible_in_invoice_cases() +
            self._tax_debt_in_refund_cases()
        )
        return cases

    def _tax_debt_correction_cases(self):
        return ['61']

    def _tax_deductible_correction_cases(self):
        return ['62']

    def _tax_advance_cases(self):
        return ['91']

    def _other_cases(self):
        cases = (
            self._tax_debt_correction_cases() +
            self._tax_deductible_correction_cases() +
            self._tax_advance_cases()
        )
        return cases

    def _get_case_domain(self, case):
        if case.code in self._invoice_base_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case.code)])
            aml_dom = [('tax_ids.id', 'in', taxes.ids)]
        elif case.code in self._invoice_tax_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case.code)])
            aml_dom = [('tax_line_id.id', 'in', taxes.ids)]
            # special case to support invoices containing
            # only deductible VAT.
            # This is an undocumented feature of this module
            # since we recommend to add such a line into the invoice tax
            # window (via the 'account_invoice_tax_manual' module).
            if case.code == '59':
                aml_dom = ['|', ('tax_ids.code', '=', 'VAT-V59')] + aml_dom
        elif case.code in self._other_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case.code)])
            aml_dom = ['|', ('tax_line_id.id', 'in', taxes.ids),
                       ('tax_ids.id', 'in', taxes.ids)]
        else:
            raise UserError(_(
                "Configuration error for tax case %s")
                % case.code)
        # TODO:
        # PR to Odoo for adding inv_type as stored related field in aml
        # so that we can improve the read_group query peformance
        inv_type = False
        if case.code in (self._base_out_invoice_cases() +
                         self._tax_debt_out_invoice_cases()):
            inv_type = 'out_invoice'
        elif case.code in (self._base_out_refund_cases() +
                           self._tax_deductible_out_refund_cases()):
            inv_type = 'out_refund'
        elif case.code in (self._base_in_invoice_cases() +
                           self._tax_debt_in_invoice_cases() +
                           self._tax_deductible_in_invoice_cases()):
            inv_type = 'in_invoice'
        elif case.code in (self._base_in_refund_cases() +
                           self._tax_debt_in_refund_cases()):
            inv_type = 'in_refund'
        if inv_type:
            if inv_type in ['out_refund']:
                # POS orders may not have an invoice but are
                # posted in a sale journal hence we need to filter out
                # the credit note cases for 'no invoice' entries in sale
                # journals.
                inv_type_args = [
                    '|',
                    ('invoice_id.type', '=', inv_type),
                    '&',
                    ('invoice_id', '=', False),
                    ('journal_id.type', '!=', 'sale')
                ]
            else:
                inv_type_args = [
                    '|',
                    ('invoice_id.type', '=', inv_type),
                    ('invoice_id', '=', False),
                ]
            aml_dom = ['&'] + aml_dom + inv_type_args
        return aml_dom

    def _calc_parent_case_amount(self, case, amounts):
        if case.id not in amounts:
            for child in case.child_ids:
                if child.id not in amounts:
                    self._calc_parent_case_amount(child, amounts)
            amounts[case.id] = sum(
                [x.factor * amounts[x.id] for x in case.child_ids])

    def _get_case_amounts(self, case_root):
        cases = case_root.search(
            [('parent_id', 'child_of', case_root.id),
             ('child_ids', '=', False)])
        amounts = {}
        date_dom = self._get_move_line_date_domain()
        for case in cases:
            aml_dom = date_dom + self._get_case_domain(case)
            flds = ['partner_id', 'debit', 'credit']
            groupby = []
            amt = self.env['account.move.line'].read_group(
                aml_dom, flds, groupby)[0]

            if case.code in (self._base_out_invoice_cases() +
                             self._base_in_refund_cases() +
                             self._tax_debt_out_invoice_cases() +
                             self._tax_debt_in_invoice_cases() +
                             self._tax_debt_in_refund_cases()):
                debit_factor = credit_factor = -1
            elif case.code in (self._base_in_invoice_cases() +
                               self._base_out_refund_cases() +
                               self._base_in_invoice_refund_cases() +
                               self._tax_deductible_in_invoice_cases() +
                               self._tax_deductible_out_refund_cases()):
                debit_factor = credit_factor = 1
            elif case.code in self._tax_debt_correction_cases():
                debit_factor = 1
                credit_factor = 0
            elif case.code in self._tax_deductible_correction_cases():
                debit_factor = 0
                credit_factor = -1
            elif case.code in self._tax_advance_cases():
                debit_factor = credit_factor = 1

            amounts[case.id] = self.currency_id.round(
                debit_factor * (amt['debit'] or 0.0) -
                credit_factor * (amt['credit'] or 0.0))

        self._calc_parent_case_amount(case_root, amounts)

        return amounts

    def _get_case_child(self, case, level, case_vals, case_amounts):
        case_vals.append({
            'case_id': case.id,
            'level': level,
            'active': not case.invisible,
            'amount': case_amounts.get(case.id, 0.0),
        })
        for child in case.child_ids:
            self._get_case_child(child, level + 1, case_vals, case_amounts)

    def _get_case_vals(self):
        case_root = self.env['account.tax.code.chart'].search(
            [('country_id', '=', self.env.ref('base.be').id),
             ('parent_id', '=', False)])
        if len(case_root) != 1:
            raise UserError(_(
                "Incorrect Belgian Tax Tag Code Chart."
                "\nReport this problem via your Odoo support "
                "partner."))

        case_amounts = self._get_case_amounts(case_root)

        case_vals = []
        level = 0
        for child in case_root.child_ids:
            self._get_case_child(child, level, case_vals, case_amounts)
        return case_vals

    def _node_VATDeclaration(self, parent, ns_map, ref):

        VATDeclaration = etree.SubElement(
            parent, 'VATDeclaration',
            attrib={
                'SequenceNumber': '1',
                'DeclarantReference': ref,
            }
        )

        # ReplacedVATDeclaration not supported at this point in time
        # TODO:
        # Create object to save legal VAT declarations in order to
        # and add support of replacements.
        # self._node_ReplacedVATDeclaration(
        #     VATDeclaration, ns_map, replace_ref)

        self._node_Declarant(VATDeclaration, ns_map)
        self._node_Period(VATDeclaration, ns_map)

        # Deduction not supported at this point in time
        # self._node_Deduction(VATDeclaration, ns_map)

        self._node_Data(VATDeclaration, ns_map)

        ClientListingNihil = etree.SubElement(
            VATDeclaration, 'ClientListingNihil')
        ClientListingNihil.text = self.client_nihil and 'YES' or 'NO'

        etree.SubElement(
            VATDeclaration, 'Ask',
            attrib={
                'Restitution': self.ask_restitution and 'YES' or 'NO',
                'Payment': self.ask_payment and 'YES' or 'NO',
            }
        )

        # TODO: add support for attachments
        # self._node_FileAttachment(parent, ns_map)

        self._node_Comment(VATDeclaration, ns_map)

        # Justification not supported at this point in time

    def _get_grid_list(self):

        grid_list = []
        for entry in self.case_ids:
            if entry.case_id.code in self._intervat_cases():
                if self.currency_id.round(entry.amount):
                    grid_list.append({
                        'grid': int(entry.case_id.code),
                        'amount': entry.amount})
            elif entry.case_id.code == 'VI':
                if self.currency_id.round(entry.amount) >= 0:
                    grid_list.append({
                        'grid': 71,
                        'amount': entry.amount})
                else:
                    grid_list.append({
                        'grid': 72,
                        'amount': -entry.amount})
        grid_list.sort(key=lambda k: k['grid'])
        return grid_list

    def _node_Data(self, VATDeclaration, ns_map):
        Data = etree.SubElement(VATDeclaration, 'Data')

        grid_list = self._get_grid_list()

        for entry in grid_list:
            Amount = etree.SubElement(
                Data, 'Amount',
                attrib={'GridNumber': str(entry['grid'])},
            )
            Amount.text = '%.2f' % entry['amount']


class l10nBeVatDeclarationCase(models.TransientModel):
    _name = 'l10n.be.vat.declaration.case'
    _order = 'sequence'

    declaration_id = fields.Many2one(
        comodel_name='l10n.be.vat.declaration',
        string='Periodical VAT Declaration')
    case_id = fields.Many2one(
        comodel_name='account.tax.code.chart',
        string='Case')
    amount = fields.Monetary(
        currency_field='currency_id')
    sequence = fields.Integer(
        related='case_id.sequence')
    level = fields.Integer()
    active = fields.Boolean()
    color = fields.Char(
        related='case_id.color')
    font = fields.Selection(
        related='case_id.font')
    currency_id = fields.Many2one(
        related='declaration_id.currency_id',
        readonly=1)

    @api.multi
    def view_move_lines(self):
        self.ensure_one()
        act_window = self.declaration_id._move_lines_act_window()
        date_dom = self.declaration_id._get_move_line_date_domain()
        if self.case_id.child_ids:
            case_dom = []
            cases = self.case_id.search(
                [('parent_id', 'child_of', self.case_id.id),
                 ('child_ids', '=', False)])
            for i, case in enumerate(cases, start=1):
                if i != len(cases):
                    case_dom += ['|']
                case_dom += self.declaration_id._get_case_domain(case)
        else:
            case_dom = self.declaration_id._get_case_domain(self.case_id)
        act_window['domain'] = date_dom + case_dom
        return act_window


class l10nBeVatDeclarationXlsx(AbstractReportXlsx):

    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, workbook, data, declaration):

        col_specs = {
            'case': {
                'header': {
                    'value': self._('Case'),
                },
                'lines': {
                    'value': self._render("c.case_id.code"),
                },
                'width': 8,
            },
            'name': {
                'header': {
                    'value': self._('Description'),
                },
                'lines': {
                    'value': self._render("c.case_id.name"),
                },
                'width': 70,
            },
            'amount': {
                'header': {
                    'value': self._('Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("c.amount"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
        }
        wanted_list = ['case', 'name', 'amount']

        return [{
            'ws_name': 'vat_declaration_%s' % declaration.period,
            'generate_ws_method': '_generate_declaration',
            'title': declaration._description,
            'wanted_list': wanted_list,
            'col_specs': col_specs,
        }]

    def _generate_declaration(self, workbook, ws, ws_params, data,
                              declaration):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._declaration_title(ws, row_pos, ws_params, data,
                                          declaration)
        row_pos = self._declaration_info(ws, row_pos, ws_params, data,
                                         declaration)
        row_pos = self._declaration_lines(ws, row_pos, ws_params, data,
                                          declaration)

    def _declaration_title(self, ws, row_pos, ws_params, data, declaration):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _declaration_info(self, ws, row_pos, ws_params, data, declaration):
        ws.write_string(row_pos, 1, self._('Company') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, declaration.company_id.name)
        row_pos += 1
        ws.write_string(row_pos, 1, self._('VAT Number') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, declaration.company_id.vat)
        row_pos += 1
        ws.write_string(row_pos, 1, self._('Period') + ':',
                        self.format_left_bold)
        ws.write_string(row_pos, 2, declaration.period)
        return row_pos + 2

    def _declaration_lines(self, ws, row_pos, ws_params, data, declaration):

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        for c in declaration.case_ids:
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={'c': c},
                default_format=self.format_tcell_left)

        return row_pos + 1


l10nBeVatDeclarationXlsx(
    'report.l10n_be_coa_multilang.report_l10n_be_vat_declaration_xlsx',
    'l10n.be.vat.declaration',
    parser=report_sxw.rml_parse)
