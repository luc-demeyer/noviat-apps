# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
from openerp.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)

_INTRASTAT_XMLNS = 'http://www.onegate.eu/2010-01-01'


class L10nBeIntrastatProductDeclaration(models.Model):
    _name = 'l10n.be.intrastat.product.declaration'
    _description = "Intrastat Product Declaration for Belgium"
    _inherit = ['intrastat.product.declaration', 'mail.thread']

    computation_line_ids = fields.One2many(
        'l10n.be.intrastat.product.computation.line',
        'parent_id', string='Intrastat Product Computation Lines',
        states={'done': [('readonly', True)]})
    declaration_line_ids = fields.One2many(
        'l10n.be.intrastat.product.declaration.line',
        'parent_id', string='Intrastat Product Declaration Lines',
        states={'done': [('readonly', True)]})

    def _get_intrastat_transaction(self, inv_line):
        transaction = super(
            L10nBeIntrastatProductDeclaration, self
        )._get_intrastat_transaction(inv_line)
        if not transaction:
            module = __name__.split('addons.')[1].split('.')[0]
            transaction = self.env.ref(
                '%s.intrastat_transaction_1' % module)
        return transaction

    def _get_region(self, inv_line):
        region = super(
            L10nBeIntrastatProductDeclaration, self)._get_region(inv_line)
        if not region:
            msg = _(
                "The Intrastat Region of the Company is not set, "
                "please configure it first.")
            self._company_warning(msg)
        return region

    def _handle_refund(self, inv_line, line_vals):
        invoice = inv_line.invoice_id
        return_picking = invoice.picking_ids
        if return_picking:

            if invoice.type == 'in_refund':
                if self.type == 'arrivals':
                    if self.company_id.intrastat_dispatches == 'exempt':
                        line_vals.update({
                            'hs_code_id': self._credit_note_code.id,
                            'region_id': invoice.src_dest_region_id.id,
                            'transaction_id': False,
                        })
                    else:
                        line_vals.clear()
                else:
                    line_vals.update({
                        'region_id': invoice.src_dest_region_id.id,
                        'transaction_id': self._transaction_2.id,
                    })

            else:  # 'out_refund':
                if self.type == 'dispatches':
                    if self.company_id.intrastat_arrivals == 'exempt':
                        line_vals.update({
                            'hs_code_id': self._credit_note_code.id,
                            'region_id': invoice.src_dest_region_id.id,
                            'transaction_id': False,
                        })
                    else:
                        line_vals.clear()
                else:
                    line_vals.update({
                        'region_id': invoice.src_dest_region_id.id,
                        'transaction_id': self._transaction_2.id,
                    })
        else:
            # Manual correction of the declaration lines can be required
            # when the sum of the computation lines results in
            # negative values
            line_vals.update({
                'weight': -line_vals['weight'],
                'suppl_unit_qty': -line_vals['suppl_unit_qty'],
                'amount_company_currency': -line_vals[
                    'amount_company_currency'],
            })

    def _update_computation_line_vals(self, inv_line, line_vals):
        super(L10nBeIntrastatProductDeclaration, self
              )._update_computation_line_vals(inv_line, line_vals)
        # handling of refunds
        # cf. NBB/BNB Intrastat guide 2016, Part,  I - Basis, par 9.6
        inv = inv_line.invoice_id
        if inv.type in ['in_refund', 'out_refund']:
            self._handle_refund(inv_line, line_vals)

        if line_vals:
            if self.type == 'dispatches':
                vat_number = self._sanitize_vat(inv.partner_id.vat)
                if not vat_number:
                    note = "\n" + _(
                        "Missing VAT Number on partner '%s'"
                        % inv.partner_id.name_get()[0][1])
                    self._note += note
                else:
                    line_vals['vat_number'] = vat_number
            # extended declaration
            if self.reporting_level == 'extended':
                incoterm = self._get_incoterm(inv_line)
                line_vals.update({
                    'incoterm_id': incoterm.id,
                })

    def _handle_invoice_accessory_cost(
            self, invoice, lines_current_invoice,
            total_inv_accessory_costs_cc, total_inv_product_cc,
            total_inv_weight):
        """
        In Belgium accessory cost should not be added.
        cf. Intrastat guide 2015 NBB/BNB:
        If transport costs and insurance costs are included in the price
        of the goods, you do not have to make any additional calculation
        or estimate in order to deduct them. If they are separately known
        (e.g. stated on a separate line on the invoice),
        transport and insurance costs may not be included in the value of
        the goods
        """
        pass

    def _gather_invoices_init(self):
        if self.company_id.country_id.code != 'BE':
            raise UserError(
                _("The Belgian Intrastat Declaration requires "
                  "the Company's Country to be equal to 'Belgium' "
                  "(country code BE)."))

        module = __name__.split('addons.')[1].split('.')[0]

        # Special commodity codes
        # Current version implements only regular credit notes
        special_code = '99600000'
        hs_code = self.env['hs.code'].search(
            [('company_id', '=', self.company_id.id),
             ('local_code', '=', special_code)])
        if not hs_code:
            action = self.env.ref(
                '%s.intrastat_installer_action' % module)
            msg = _(
                "Intrastat Code '%s' not found. "
                "\nYou can update your codes "
                "via the Intrastat Configuration Wizard."
            ) % special_code
            raise RedirectWarning(
                msg, action.id,
                _("Go to the Intrastat Configuration Wizard."))
        self._credit_note_code = hs_code[0]

        self._transaction_2 = self.env.ref(
            '%s.intrastat_transaction_2' % module)

    def _prepare_invoice_domain(self):
        """
        Both in_ and out_refund must be included in order to cover
        - credit notes with and without return
        - companies subject to arrivals or dispatches only
        """
        domain = super(
            L10nBeIntrastatProductDeclaration, self)._prepare_invoice_domain()
        if self.type == 'arrivals':
            domain.append(
                ('type', 'in', ('in_invoice', 'in_refund', 'out_refund')))
        elif self.type == 'dispatches':
            domain.append(
                ('type', 'in', ('out_invoice', 'in_refund', 'out_refund')))
        return domain

    def _sanitize_vat(self, vat):
        return vat and vat.replace(' ', '').replace('.', '').upper()

    @api.model
    def _group_line_hashcode_fields(self, computation_line):
        res = super(
            L10nBeIntrastatProductDeclaration, self
        )._group_line_hashcode_fields(computation_line)
        if self.type == 'arrivals':
            del res['product_origin_country']
        if self.type == 'dispatches':
            res['vat_number'] = computation_line.vat_number
        if self.reporting_level == 'extended':
            res['incoterm'] = computation_line.incoterm_id.id or False
        return res

    @api.model
    def _prepare_grouped_fields(self, computation_line, fields_to_sum):
        vals = super(
            L10nBeIntrastatProductDeclaration, self
        )._prepare_grouped_fields(computation_line, fields_to_sum)
        if self.type == 'dispatches':
            vals['vat_number'] = computation_line.vat_number
        if self.reporting_level == 'extended':
            vals['incoterm_id'] = computation_line.incoterm_id.id
        return vals

    @api.one
    def _check_generate_xml(self):
        res = super(
            L10nBeIntrastatProductDeclaration, self)._check_generate_xml()
        if not self.declaration_line_ids:
            res = self.generate_declaration()
        kbo_nr = False
        if self.company_id.partner_id.registry_authority == 'kbo_bce':
            kbo_nr = self.company_id.partner_id.registry_number
        if not kbo_nr:
            raise UserError(
                _("Configuration Error."),
                _("No KBO/BCE Number defined for your Company."))
        return res

    def _node_Admininstration(self, parent):
        Administration = etree.SubElement(parent, 'Administration')
        From = etree.SubElement(Administration, 'From')
        From.text = self.company_id.partner_id.registry_number.replace('.', '')
        From.set('declarerType', 'KBO')
        etree.SubElement(Administration, 'To').text = "NBB"
        etree.SubElement(Administration, 'Domain').text = "SXX"

    def _node_Item(self, parent, line):
        Item = etree.SubElement(parent, 'Item')
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXTRF'}
        ).text = self._decl_code
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXCNT'}
        ).text = line.src_dest_country_id.code
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXTTA'}
        ).text = line.transaction_id.code
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXREG'}
        ).text = line.region_id.code
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXTGO'}
        ).text = line.hs_code_id.local_code
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXWEIGHT'}
        ).text = str(line.weight)
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXUNITS'}
        ).text = str(line.suppl_unit_qty)
        etree.SubElement(
            Item, 'Dim',
            attrib={'prop': 'EXTXVAL'}
        ).text = str(line.amount_company_currency)
        if self.type == 'dispatches':
            etree.SubElement(
                Item, 'Dim',
                attrib={'prop': 'EXCNTORI'}
            ).text = line.product_origin_country_id.code or 'QU'
            etree.SubElement(
                Item, 'Dim',
                attrib={'prop': 'PARTNERID'}
            ).text = line.vat_number or ''
        if self.reporting_level == 'extended':
            etree.SubElement(
                Item, 'Dim',
                attrib={'prop': 'EXTPC'}
            ).text = line.transport_id.code
            etree.SubElement(
                Item, 'Dim',
                attrib={'prop': 'EXDELTRM'}
            ).text = line.incoterm_id.code

    def _node_Data(self, parent):
        Data = etree.SubElement(parent, 'Data')
        Data.set('close', 'true')
        if self.type == 'arrivals':
            report_form = 'EXF19%s'
        else:
            report_form = 'INTRASTAT_X_%sF'
        if self.reporting_level == 'standard':
            report_form = report_form % 'S'
        else:
            report_form = report_form % 'E'
        Data.set('form', report_form)
        if self.action != 'nihil':
            for line in self.declaration_line_ids:
                self._node_Item(Data, line)

    def _node_Report(self, parent):
        Report = etree.SubElement(parent, 'Report')
        Report.set('action', self.action)
        Report.set('date', self.year_month)
        if self.type == 'arrivals':
            report_code = 'EX19'
        else:
            report_code = 'INTRASTAT_X_'
        if self.reporting_level == 'standard':
            report_code += 'S'
        else:
            report_code += 'E'
        Report.set('code', report_code)
        self._node_Data(Report)

    @api.multi
    def _generate_xml(self):

        if self.type == 'arrivals':
            self._decl_code = '19'
            if self.reporting_level == 'standard':
                xsd = 'ex19s'
            else:
                xsd = 'ex19e'
        else:
            self._decl_code = '29'
            if self.reporting_level == 'standard':
                xsd = 'intrastat_x_s'
            else:
                xsd = 'intrastat_x_e'

        ns_map = {
            None: _INTRASTAT_XMLNS,
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        }
        root = etree.Element('DeclarationReport', nsmap=ns_map)
        self._node_Admininstration(root)
        self._node_Report(root)

        xml_string = etree.tostring(
            root, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        module = __name__.split('addons.')[1].split('.')[0]
        self._check_xml_schema(
            xml_string,
            '%s/data/%s.xsd' % (module, xsd)
        )
        return xml_string


class L10nBeIntrastatProductComputationLine(models.Model):
    _name = 'l10n.be.intrastat.product.computation.line'
    _inherit = 'intrastat.product.computation.line'

    parent_id = fields.Many2one(
        comodel_name='l10n.be.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    declaration_line_id = fields.Many2one(
        comodel_name='l10n.be.intrastat.product.declaration.line',
        string='Declaration Line', readonly=True)
    vat_number = fields.Char(
        string='VAT Number',
        help="VAT number of the trading partner")


class L10nBeIntrastatProductDeclarationLine(models.Model):
    _name = 'l10n.be.intrastat.product.declaration.line'
    _inherit = 'intrastat.product.declaration.line'

    parent_id = fields.Many2one(
        comodel_name='l10n.be.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    computation_line_ids = fields.One2many(
        comodel_name='l10n.be.intrastat.product.computation.line',
        inverse_name='declaration_line_id',
        string='Computation Lines', readonly=True)
    vat_number = fields.Char(
        string='VAT Number',
        help="VAT number of the trading partner")
