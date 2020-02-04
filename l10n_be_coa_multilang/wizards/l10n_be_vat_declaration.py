# Copyright 2009-2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from lxml import etree
import time

from odoo import api, fields, models, _
from odoo.tools.translate import translate
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
        warnings = [x for x in negative_cases
                    if x.case_id.code in self._intervat_cases()]
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
        report_file = 'vat_declaration_%s' % self.period
        module = __name__.split('addons.')[1].split('.')[0]
        report_name = '{}.vat_declaration_xls'.format(module)
        report = {
            'name': _('Periodical VAT Declaration'),
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'report_file': report_name,
            'context': dict(self.env.context, report_file=report_file),
            'data': {'dynamic_report': True},
        }
        return report

    @api.multi
    def create_detail_xls(self):
        report_file = 'vat_detail_%s' % self.period
        module = __name__.split('addons.')[1].split('.')[0]
        report_name = '{}.vat_detail_xls'.format(module)
        report = {
            'name': _('Periodical VAT Declaration details'),
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'report_file': report_name,
            'context': dict(self.env.context, report_file=report_file),
            'data': {'dynamic_report': True},
        }
        return report

    @api.multi
    def create_xml(self):
        """
        Intervat XML Periodical VAT Declaration.
        TODO: add support for 'Representative' (Mandataris)
        """

        ns_map = {
            None: 'http://www.minfin.fgov.be/VATConsignment',
            'ic': 'http://www.minfin.fgov.be/InputCommon',
        }

        Doc = etree.Element(
            'VATConsignment',
            attrib={'VATDeclarationsNbr': '1'},
            nsmap=ns_map)

        # self._node_Representative(Doc, ns_map)
        ref = self._get_declaration_ref()
        # self._node_RepresentativeReference(Doc, ns_map, ref)

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
        return self.env.ref(
            '%s.action_report_l10nbevatdeclaration' % module
            ).report_action(self)

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

    def _get_tax_map(self):
        """
        :return: dict
            key: id of account.tax object
            value: list of tuples, fuple fields
                0: aml_check
                1: tax code
                2: debit_factor
                3: credit_factor
        """
        tax_map = {}
        be_tax_codes = self._intervat_cases()
        taxes = self.env[
            'account.tax'].with_context(active_test=False).search([])
        for tax in taxes:
            tag_codes = tax.tag_ids.mapped('code')
            tag_codes_2 = [x[:2] for x in tag_codes]
            if any([x in be_tax_codes for x in tag_codes_2]):
                tax_map[tax.id] = []
            else:
                continue
            for tc in tag_codes:
                debit_factor, credit_factor = self._get_case_factors(tc)
                aml_check = self._get_case_domain(tc, get_domain=False)
                tax_map[tax.id].append(
                    (aml_check, tc, debit_factor, credit_factor))
        return tax_map

    def _get_case_domain(self, case_code, get_domain=True):
        """
        :return:
            account.move.line domain if get_domain=True
            else account.move.line condition
        """
        if case_code in self._invoice_base_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case_code)])
            aml_dom = [('tax_ids.id', 'in', taxes.ids)]
            aml_check = '{aml}.tax_ids'
        elif case_code in self._invoice_tax_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case_code)])
            aml_dom = [('tax_line_id.id', 'in', taxes.ids)]
            aml_check = '{aml}.tax_line_id'
            # special case to support invoices containing
            # only deductible VAT.
            # This is an undocumented feature of this module
            # since we recommend to add such a line into the invoice tax
            # window (via the 'account_invoice_tax_manual' module).
            if case_code == '59':
                aml_dom = ['|', ('tax_ids.code', '=', 'VAT-V59')] + aml_dom
                aml_check = "{aml}.tax_ids.code == 'VAT-V59' or " + aml_check
        elif case_code in self._other_cases():
            taxes = self.env['account.tax'].search(
                [('tag_ids.code', '=', case_code)])
            aml_dom = ['|', ('tax_line_id.id', 'in', taxes.ids),
                       ('tax_ids.id', 'in', taxes.ids)]
            aml_check = '{aml}.tax_line_id or {aml}.tax_ids'
        else:
            raise UserError(_(
                "Configuration error for tax case %s")
                % case_code)
        # TODO:
        # PR to Odoo for adding inv_type as stored related field in aml
        # so that we can improve the read_group query peformance
        inv_type = False
        if case_code in (self._base_out_invoice_cases() +
                         self._tax_debt_out_invoice_cases()):
            inv_type = 'out_invoice'
        elif case_code in (self._base_out_refund_cases() +
                           self._tax_deductible_out_refund_cases()):
            inv_type = 'out_refund'
        elif case_code in (self._base_in_invoice_cases() +
                           self._tax_debt_in_invoice_cases() +
                           self._tax_deductible_in_invoice_cases()):
            inv_type = 'in_invoice'
        elif case_code in (self._base_in_refund_cases() +
                           self._tax_debt_in_refund_cases()):
            inv_type = 'in_refund'
        if inv_type:
            if inv_type in ['out_refund']:
                # filter out refund cases when the Journal Item
                # has no originating invoice, e.g.
                # POS Orders, misc. operations
                inv_type_args = [
                    '|',
                    ('invoice_id.type', '=', inv_type),
                    '&',
                    ('invoice_id', '=', False),
                    ('debit', '>', 0)
                ]
                inv_check = (
                    "({aml}.invoice_id.type == '%s'"
                    " or "
                    "(not {aml}.invoice_id and ({aml}.debit > 0)))"
                ) % inv_type
            elif inv_type in ['in_refund']:
                # filter out refund cases when the Journal Item
                # has no originating invoice, e.g.
                # bank costs, expense notes, misc. operations
                inv_type_args = [
                    '|',
                    ('invoice_id.type', '=', inv_type),
                    '&',
                    ('invoice_id', '=', False),
                    ('credit', '>', 0),
                ]
                inv_check = (
                    "({aml}.invoice_id.type == '%s'"
                    " or "
                    "(not {aml}.invoice_id and ({aml}.credit > 0)))"
                ) % inv_type
            else:
                inv_type_args = [
                    '|',
                    ('invoice_id.type', '=', inv_type),
                    ('invoice_id', '=', False),
                ]
                inv_check = (
                    "({aml}.invoice_id.type == '%s'"
                    " or not {aml}.invoice_id)"
                ) % inv_type
            aml_dom = ['&'] + aml_dom + inv_type_args
            aml_check = aml_check + ' and ' + inv_check
        return get_domain and aml_dom or aml_check

    def _calc_parent_case_amount(self, case, amounts):
        if case.id not in amounts:
            for child in case.child_ids:
                if child.id not in amounts:
                    self._calc_parent_case_amount(child, amounts)
            amounts[case.id] = sum(
                [x.factor * amounts[x.id] for x in case.child_ids])

    def _get_case_factors(self, case_code):
        if case_code in (self._base_out_invoice_cases() +
                         self._base_in_refund_cases() +
                         self._tax_debt_out_invoice_cases() +
                         self._tax_debt_in_invoice_cases() +
                         self._tax_debt_in_refund_cases()):
            debit_factor = credit_factor = -1
        elif case_code in (self._base_in_invoice_cases() +
                           self._base_out_refund_cases() +
                           self._base_in_invoice_refund_cases() +
                           self._tax_deductible_in_invoice_cases() +
                           self._tax_deductible_out_refund_cases()):
            debit_factor = credit_factor = 1
        elif case_code in self._tax_debt_correction_cases():
            debit_factor = 1
            credit_factor = 0
        elif case_code in self._tax_deductible_correction_cases():
            debit_factor = 0
            credit_factor = -1
        elif case_code in self._tax_advance_cases():
            debit_factor = credit_factor = 1
        return debit_factor, credit_factor

    def _get_case_amounts(self, case_root):
        cases = case_root.search(
            [('parent_id', 'child_of', case_root.id),
             ('child_ids', '=', False)])
        amounts = {}
        date_dom = self._get_move_line_date_domain()
        for case in cases:
            aml_dom = date_dom + self._get_case_domain(case.code)
            flds = ['partner_id', 'debit', 'credit']
            groupby = []
            amt = self.env['account.move.line'].read_group(
                aml_dom, flds, groupby)[0]
            debit_factor, credit_factor = self._get_case_factors(case.code)
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
    _description = 'Periodical VAT Declaration line'

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
                case_dom += self.declaration_id._get_case_domain(case.code)
        else:
            case_dom = self.declaration_id._get_case_domain(self.case_id.code)
        act_window['domain'] = date_dom + case_dom
        return act_window


class l10nBeVatDeclarationXlsx(models.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.vat_declaration_xls'
    _inherit = 'report.report_xlsx.abstract'

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
        ws.write_string(row_pos, 2, declaration.company_id.vat or '')
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


class l10nBeVatDetailXlsx(models.AbstractModel):
    _name = 'report.l10n_be_coa_multilang.vat_detail_xls'
    _inherit = 'report.report_xlsx.abstract'

    #TODO: add xlats for this report
    def _(self, src):
        lang = self.env.context.get('lang', 'en_US')
        val = translate(
            self.env.cr, IR_TRANSLATION_NAME, 'report', lang, src) or src
        return val

    def _get_ws_params(self, wb, data, decl):
        self._date_dom = decl._get_move_line_date_domain()
        flds = ['journal_id', 'debit']
        groupby = ['journal_id']
        totals = self.env['account.move.line'].read_group(
            self._date_dom, flds, groupby)
        j_dict = {}
        for entry in totals:
            if entry['debit']:
                j_dict[entry['journal_id'][0]] = entry['debit']
        j_ids = list(j_dict.keys())
        self._journal_totals = j_dict
        # search i.s.o. browse for account.journal _order
        self._journals = self.env['account.journal'].search(
            [('id', 'in', j_ids)])
        slist = [self._get_centralisation_ws_params(wb, data, decl)]
        for journal in self._journals:
            slist.append(self._get_journal_ws_params(wb, data, decl, journal))
        return slist

    def _get_centralisation_ws_params(self, wb, data, decl):

        col_specs = {
            'code': {
                'header': {
                    'value': self._('Code'),
                },
                'lines': {
                    'value': self._render("journal.code"),
                },
                'width': 10,
            },
            'name': {
                'header': {
                    'value': self._('Journal'),
                },
                'lines': {
                    'value': self._render("journal.name"),
                },
                'width': 45,
            },
            'debit': {
                'header': {
                    'value': self._('Total Debit/Credit'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'type': 'number',
                    'value': self._render("debit"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render('total_debit_formula'),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 20,
            },
        }
        wl = ['code', 'name', 'debit']

        title = (10 * ' ').join([
            decl.company_id.name, _('Journal Centralisation'), decl.period])

        return {
            'ws_name': self._('Centralisation'),
            'generate_ws_method': '_centralisation_report',
            'title': title,
            'wanted_list': wl,
            'col_specs': col_specs,
        }

    def _centralisation_report(self, wb, ws, ws_params, data, decl):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._centralisation_title(ws, row_pos, ws_params, data,
                                             decl)
        row_pos = self._centralisation_lines(ws, row_pos, ws_params, data,
                                             decl)

    def _centralisation_title(self, ws, row_pos, ws_params, data, decl):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _centralisation_lines(self, ws, row_pos, ws_params, data, decl):

        wl = ws_params['wanted_list']
        debit_pos = wl.index('debit')
        start_pos = row_pos + 1

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        for journal in self._journals:
            debit = self._journal_totals[journal.id]
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={
                    'journal': journal,
                    'debit': debit,
                },
                default_format=self.format_tcell_left)

        debit_start = self._rowcol_to_cell(start_pos, debit_pos)
        debit_stop = self._rowcol_to_cell(row_pos - 1, debit_pos)
        total_debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'total_debit_formula': total_debit_formula,
            },
            default_format=self.format_theader_yellow_left)

        return row_pos + 1

    def _get_journal_template(self):
        template = {
            'move_name': {
                'header': {
                    'value': self._('Entry'),
                },
                'lines': {
                    'value': self._render(
                        "l.move_id.name != '/' and l.move_id.name "
                        "or ('*' + str(l.move_id))"),
                },
                'width': 20,
            },
            'move_date': {
                'header': {
                    'value': self._('Effective Date'),
                },
                'lines': {
                    'value': self._render(
                        "datetime.strptime(l.date, '%Y-%m-%d')"),
                    'format': self.format_tcell_date_left,
                },
                'width': 13,
            },
            'acc_code': {
                'header': {
                    'value': self._('Account'),
                },
                'lines': {
                    'value': self._render(
                        "l.account_id.code"),
                },
                'width': 12,
            },
            'acc_name': {
                'header': {
                    'value': self._('Account Name'),
                },
                'lines': {
                    'value': self._render(
                        "l.account_id.name"),
                },
                'width': 36,
            },
            'aml_name': {
                'header': {
                    'value': self._('Name'),
                },
                'lines': {
                    'value': self._render("l.name"),
                },
                'width': 42,
            },
            'journal_code': {
                'header': {
                    'value': self._('Journal'),
                },
                'lines': {
                    'value': self._render("l.journal_id.code"),
                },
                'width': 10,
            },
            'journal': {
                'header': {
                    'value': self._('Journal'),
                },
                'lines': {
                    'value': self._render("l.journal_id.name"),
                },
                'width': 20,
            },
            'analytic_account_name': {
                'header': {
                    'value': self._('Analytic Account'),
                },
                'lines': {
                    'value': self._render(
                        "l.analytic_account_id "
                        "and l.analytic_account_id.name"),
                },
                'width': 20,
            },
            'analytic_account_code': {
                'header': {
                    'value': self._('Analytic Account Reference'),
                },
                'lines': {
                    'value': self._render(
                        "l.analytic_account_id "
                        "and l.analytic_account_id.code or ''"),
                },
                'width': 20,
            },
            'partner_name': {
                'header': {
                    'value': self._('Partner'),
                },
                'lines': {
                    'value': self._render(
                        "l.partner_id and l.partner_id.name"),
                },
                'width': 36,
            },
            'partner_ref': {
                'header': {
                    'value': self._('Partner Reference'),
                },
                'lines': {
                    'value': self._render(
                        "l.partner_id and l.partner_id.ref or ''"),
                },
                'width': 10,
            },
            'date_maturity': {
                'header': {
                    'value': self._('Maturity Date'),
                },
                'lines': {
                    'value': self._render(
                        "datetime.strptime(l.date_maturity,'%Y-%m-%d')"),
                    'format': self.format_tcell_date_left,
                },
                'width': 13,
            },
            'debit': {
                'header': {
                    'value': self._('Debit'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l.debit"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("debit_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'credit': {
                'header': {
                    'value': self._('Credit'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l.credit"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("credit_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'balance': {
                'header': {
                    'value': self._('Balance'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l.balance"),
                    'format': self.format_tcell_amount_right,
                },
                'totals': {
                    'type': 'formula',
                    'value': self._render("bal_formula"),
                    'format': self.format_theader_yellow_amount_right,
                },
                'width': 18,
            },
            'full_reconcile': {
                'header': {
                    'value': self._('Rec.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render(
                        "l.full_reconcile_id "
                        "and l.full_reconcile_id.name"),
                    'format': self.format_tcell_center,
                },
                'width': 12,
            },
            'reconcile_amount': {
                'header': {
                    'value': self._('Reconcile Amount'),
                },
                'lines': {
                    'value': self._render(
                        "l.full_reconcile_id and l.balance or "
                        "(sum(l.matched_credit_ids.mapped('amount')) - "
                        "sum(l.matched_debit_ids.mapped('amount')))"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 12,
            },
            'tax_code': {
                'header': {
                    'value': self._('VAT'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render("tax_code"),
                    'format': self.format_tcell_center,
                },
                'width': 10,
            },
            'tax_amount': {
                'header': {
                    'value': self._('VAT Amount'),
                },
                'lines': {
                    'value': self._render("tax_amount"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
            'amount_currency': {
                'header': {
                    'value': self._('Am. Currency'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("l.amount_currency"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
            'currency_name': {
                'header': {
                    'value': self._('Curr.'),
                    'format': self.format_theader_yellow_center,
                },
                'lines': {
                    'value': self._render(
                        "l.currency_id and l.currency_id.name"),
                    'format': self.format_tcell_center,
                },
                'width': 6,
            },
            'move_ref': {
                'header': {
                    'value': self._('Entry Reference'),
                },
                'lines': {
                    'value': self._render("l.move_id.name"),
                },
                'width': 25,
            },
            'move_id': {
                'header': {
                    'value': self._('Entry Ide'),
                },
                'lines': {
                    'value': self._render("str(l.move_id.id)"),
                },
                'width': 10,
            },
        }
        return template

    def _get_vat_summary_template(self):
        """
        XLS Template VAT Summary
        """
        template = {
            'tax_code': {
                'header': {
                    'value': self._('Case'),
                },
                'lines': {
                    'value': self._render("tc"),
                },
                'width': 6,
            },
            'tax_amount': {
                'header': {
                    'value': self._('Amount'),
                    'format': self.format_theader_yellow_right,
                },
                'lines': {
                    'value': self._render("tax_totals[tc]"),
                    'format': self.format_tcell_amount_right,
                },
                'width': 18,
            },
        }
        return template

    def _get_journal_ws_params(self, wb, data, decl, journal):
        col_specs = self._get_journal_template()
        col_specs.update(self.env['account.journal']._report_xlsx_template())
        wl = self.env['account.journal']._report_xlsx_fields()
        title = (10 * ' ').join([
            decl.company_id.name,
            journal.name + '({})'.format(journal.code),
            decl.period])
        ws_params_summary = {
            'col_specs': self._get_vat_summary_template(),
            'wanted_list': ['tax_code', 'tax_amount'],
        }
        return {
            'ws_name': journal.code,
            'generate_ws_method': '_journal_report',
            'title': title,
            'wanted_list': wl,
            'col_specs': col_specs,
            'ws_params_summary': ws_params_summary,
            'journal': journal,
        }

    def _journal_report(self, wb, ws, ws_params, data, decl):

        time_start = time.time()
        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        journal = ws_params['journal']
        row_pos = self._journal_title(ws, row_pos, ws_params, data,
                                      decl, journal)
        row_pos = self._journal_lines(ws, row_pos, ws_params, data,
                                      decl, journal)
        time_end = time.time() - time_start
        _logger.debug(
            "VAT Transaction report processing time for "
            "Journal %s = %.3f seconds",
            journal.code, time_end)

    def _journal_title(self, ws, row_pos, ws_params, data, decl, journal):
        return self._write_ws_title(ws, row_pos, ws_params)

    def _journal_lines(self, ws, row_pos, ws_params, data, decl, journal):

        wl = ws_params['wanted_list']
        debit_pos = wl.index('debit')
        credit_pos = wl.index('credit')
        start_pos = row_pos + 1

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='header',
            default_format=self.format_theader_yellow_left)

        ws.freeze_panes(row_pos, 0)

        am_dom = self._date_dom + [('journal_id', '=', journal.id)]
        ams = self.env['account.move'].search(
            am_dom, order='name, date')
        amls = ams.mapped('line_ids')

        tax_totals = {}
        tax_map = decl._get_tax_map()
        cround = decl.company_id.currency_id.round
        for aml in amls:
            tax_codes = ''
            tax_amount = None
            aml_taxes = aml.tax_ids | aml.tax_line_id
            for tax in aml_taxes:
                if tax.id not in tax_map:
                    continue
                for entry in tax_map[tax.id]:
                    aml_check = eval(entry[0].format(aml='aml'))
                    if aml_check:
                        tc = entry[1]
                        tax_amount = cround(
                            entry[2] * (aml.debit or 0.0) -
                            entry[3] * (aml.credit or 0.0))
                        if tc not in tax_totals:
                            tax_totals[tc] = tax_amount
                        else:
                            tax_totals[tc] += tax_amount
                        if tax_codes:
                            tax_codes += ', '
                        tax_codes += tc
                        if tax_amount < 0:
                            tax_codes += '(-1)'

            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='lines',
                render_space={
                    'l': aml,
                    'tax_code': tax_codes,
                    'tax_amount': tax_amount and abs(tax_amount),
                },
                default_format=self.format_tcell_left)

        debit_start = self._rowcol_to_cell(start_pos, debit_pos)
        debit_stop = self._rowcol_to_cell(row_pos - 1, debit_pos)
        debit_formula = 'SUM(%s:%s)' % (debit_start, debit_stop)
        credit_start = self._rowcol_to_cell(start_pos, credit_pos)
        credit_stop = self._rowcol_to_cell(row_pos - 1, credit_pos)
        credit_formula = 'SUM(%s:%s)' % (credit_start, credit_stop)
        debit_cell = self._rowcol_to_cell(row_pos, debit_pos)
        credit_cell = self._rowcol_to_cell(row_pos, credit_pos)
        bal_formula = debit_cell + '-' + credit_cell

        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='totals',
            render_space={
                'debit_formula': debit_formula,
                'credit_formula': credit_formula,
                'bal_formula': bal_formula,
            },
            default_format=self.format_theader_yellow_left)

        ws_params_summary = ws_params['ws_params_summary']
        row_pos += 1
        tcs = list(tax_totals.keys())
        tcs.sort()
        if tcs:
            row_pos = self._write_line(
                ws, row_pos, ws_params_summary, col_specs_section='header',
                default_format=self.format_theader_yellow_left)
            for tc in tcs:
                row_pos = self._write_line(
                    ws, row_pos, ws_params_summary, col_specs_section='lines',
                    render_space={
                        'l': aml,
                        'tc': tc,
                        'tax_totals': tax_totals
                    },
                    default_format=self.format_tcell_left)

        return row_pos + 1
