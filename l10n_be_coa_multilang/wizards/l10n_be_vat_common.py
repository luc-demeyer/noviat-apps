# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
import time
from lxml import etree
from StringIO import StringIO
from sys import exc_info
from traceback import format_exception

from odoo import api, fields, models, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError


class l10nBeVatCommon(models.AbstractModel):
    _name = 'l10n.be.vat.common'
    _description = 'Common code for Belgian VAT reports'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self._default_company_id(),
        required=True,
        string='Company')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True)
    declarant_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        string='Declarant',
        help="Select the contact for the declaration")
    year = fields.Char(
        size=4, required=True,
        default=lambda self: self._default_year())
    period_length = fields.Selection(
        selection=[('month', 'Month'),
                   ('quarter', 'Quarter')])
    month = fields.Selection(
        selection=[('01', 'Januari'),
                   ('02', 'Februari'),
                   ('03', 'March'),
                   ('04', 'April'),
                   ('05', 'May'),
                   ('06', 'June'),
                   ('07', 'July'),
                   ('08', 'August'),
                   ('09', 'September'),
                   ('10', 'October'),
                   ('11', 'November'),
                   ('12', 'December')])
    quarter = fields.Selection(
        selection=[('1', 'Q1'),
                   ('2', 'Q2'),
                   ('3', 'Q3'),
                   ('4', 'Q4')])
    period = fields.Char(
        compute='_compute_period')
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Period')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    file_name = fields.Char()
    file_save = fields.Binary(
        string='Save File', readonly=True)
    comments = fields.Text(string='Comments')
    note = fields.Text(string='Notes')

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id

    @api.model
    def _default_year(self):
        if self._name == 'l10n.be.vat.listing':
            year = str(int(time.strftime('%Y')) - 1)
        else:
            year = str(int(time.strftime('%Y')))
        return year

    @api.one
    @api.depends('year', 'period_length', 'month', 'quarter')
    def _compute_period(self):
        if self.year and self.period_length:
            if self.period_length == 'month':
                self.period = '%s-%s' % (self.year, self.month)
            else:
                self.period = '%s-Q%s' % (self.year, self.quarter)

    @api.model
    @api.constrains('year')
    def _check_year(self):
        for this in self:
            s = str(this.year)
            if len(s) != 4 or s[0] not in ['1', '2']:
                raise UserError(_("Invalid Year !"))

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            contacts = self.company_id.partner_id.child_ids.filtered(
                lambda r: r.type == 'invoice')
            self.declarant_id = contacts and contacts[0] \
                or self.company_id.partner_id
        decl_dom = [
            '|',
            ('parent_id', '=', self.company_id.id),
            ('id', '=', self.company_id.id)]
        return {'domain': {'declarant_id': decl_dom}}

    @api.onchange('year', 'period_length', 'month', 'quarter')
    def _onchange_period(self):
        if self.year:
            if self._name == 'l10n.be.vat.listing':
                self.date_from = '%s-01-01' % self.year
                self.date_to = '%s-12-31' % self.year
            elif self.period_length:
                if self.period_length == 'month' and self.month:
                    m_from = self.month
                    m_to = self.month
                elif self.period_length == 'quarter' and self.quarter:
                    i = int(self.quarter) - 1
                    m_from = ['01', '04', '07', '10'][i]
                    m_to = ['03', '06', '09', '12'][i]
                else:
                    m_from = m_to = False
                self.date_from = m_from and '%s-%s-01' % (self.year, m_from)
                d_to = m_to and calendar.monthrange(
                    int(self.year), int(m_to))[1]
                self.date_to = d_to and '%s-%s-%s' % (self.year, m_to, d_to)

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def create_xls(self):
        raise UserError(_(
            "The XLS export function is not available."))

    @api.multi
    def create_xml(self):
        raise UserError(_(
            "The XML export function is not available."))

    def _normalise_vat(self, vat):
        if vat:
            vat = vat.replace(' ', '').replace('.', '').upper()
            if vat[:2] == 'BE' and len(vat) == 11:
                vat = 'BE0' + vat[2:]
        return vat or '-'

    def _get_company_vat(self):
        cpart = self.company_id.partner_id
        company_vat = cpart.vat
        if not company_vat:
            raise UserError(_("No company VAT number"))
        company_vat = self._normalise_vat(cpart.vat)
        return company_vat

    def _get_move_line_date_domain(self):
        aml_dom = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)]
        return aml_dom

    def _get_company_data(self):
        cpart = self.company_id.partner_id
        company_vat = self._get_company_vat()

        company_street = cpart.street
        if not company_street:
            raise UserError(_(
                "No 'Street' for %s")
                % cpart.name)
        if cpart.street2:
            company_street += ' ' + cpart.street2

        company_zip = cpart.zip
        if not company_zip:
            raise UserError(_(
                "No 'ZIP Code' for %s")
                % cpart.name)

        company_city = cpart.city
        if not company_city:
            raise UserError(_(
                "No 'City' for %s")
                % cpart.name)

        company_data = {
            'vat': company_vat,
            'name': self.company_id.name,
            'street': company_street,
            'zip': company_zip,
            'city': company_city,
            'country_code': 'BE',
        }
        return company_data

    def _get_declarant_data(self):
        email = self.declarant_id.email
        if not email:
            raise UserError(_(
                "No 'email' for %s")
                % self.declarant_id.name)

        phone = self.declarant_id.phone
        if not phone:
            raise UserError(_(
                "No 'phone' for %s")
                % self.declarant_id.name)

        declarant_data = {
            'email': email,
            'phone': phone,
        }
        return declarant_data

    def _get_declaration_ref(self):
        seq = self.env['ir.sequence'].next_by_code('declarantseq')
        company_vat = self._get_company_vat()
        ref = company_vat[2:] + seq[-4:]
        return ref

    def _node_Representative(self, parent, ns_map):
        company_data = self._get_company_data()
        declarant_data = self._get_declarant_data()

        Representative = etree.SubElement(
            parent, 'Representative')

        RepresentativeID = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'RepresentativeID'),
            attrib={
                'issuedBy': company_data['country_code'],
                'identificationType': 'NVAT',
            }
        )
        RepresentativeID.text = company_data['vat'][2:]

        RepresentativeName = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'Name'),
        )
        RepresentativeName.text = company_data['name']

        RepresentativeStreet = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'Street'),
        )
        RepresentativeStreet.text = company_data['street']

        RepresentativePostCode = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'PostCode'),
        )
        RepresentativePostCode.text = company_data['zip']

        RepresentativeCity = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'City'),
        )
        RepresentativeCity.text = company_data['city']

        RepresentativeCountryCode = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'CountryCode'),
        )
        RepresentativeCountryCode.text = company_data['country_code']

        RepresentativeEmailAddress = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'EmailAddress'),
        )
        RepresentativeEmailAddress.text = declarant_data['email']

        RepresentativePhone = etree.SubElement(
            Representative,
            etree.QName(ns_map['ic'], 'Phone'),
        )
        RepresentativePhone.text = declarant_data['phone']

    def _node_RepresentativeReference(self, parent, ns_map, ref):
        RepresentativeReference = etree.SubElement(
            parent, 'RepresentativeReference')
        RepresentativeReference.text = ref

    def _node_Declarant(self, parent, ns_map):
        company_data = self._get_company_data()
        declarant_data = self._get_declarant_data()

        Declarant = etree.SubElement(parent, 'Declarant')

        DeclarantVATNumber = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'VATNumber'),
        )
        DeclarantVATNumber.text = company_data['vat'][2:]

        DeclarantName = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'Name'),
        )
        DeclarantName.text = company_data['name']

        DeclarantStreet = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'Street'),
        )
        DeclarantStreet.text = company_data['street']

        DeclarantPostCode = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'PostCode'),
        )
        DeclarantPostCode.text = company_data['zip']

        DeclarantCity = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'City'),
        )
        DeclarantCity.text = company_data['city']

        DeclarantCountryCode = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'CountryCode'),
        )
        DeclarantCountryCode.text = company_data['country_code']

        DeclarantEmailAddress = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'EmailAddress'),
        )
        DeclarantEmailAddress.text = declarant_data['email']

        DeclarantPhone = etree.SubElement(
            Declarant,
            etree.QName(ns_map['ic'], 'Phone'),
        )
        DeclarantPhone.text = declarant_data['phone']

    def _node_Period(self, parent, ns_map):
        Period = etree.SubElement(parent, 'Period')
        if self.period_length == 'month':
            Month = etree.SubElement(Period, 'Month')
            Month.text = self.month
        else:
            Quarter = etree.SubElement(Period, 'Quarter')
            Quarter.text = self.quarter
        Year = etree.SubElement(Period, 'Year')
        Year.text = str(self.year)

    def _node_Comment(self, parent, ns_map):
        if self.comments:
            Comment = etree.SubElement(parent, 'Comment')
            Comment.text = self.comments

    def _validate_xmlschema(self, xml_string, xsd):
        module = __name__.split('addons.')[1].split('.')[0]
        path = get_module_resource(module, 'schemas', xsd)
        try:
            schema = etree.XMLSchema(etree.parse(open(path)))
            t = etree.parse(StringIO(xml_string))
            schema.assertValid(t)
        except (etree.XMLSchemaParseError, etree.DocumentInvalid) as e:
            raise UserError('%s\n\n%s' % (e.__class__.__name__, e.message))
        except:
            error = _("Unknown Error")
            tb = ''.join(format_exception(*exc_info()))
            error += '\n%s' % tb
            raise UserError(error)

    def _action_save_xml(self):
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.l10n_be_vat_common_view_form_xml' % module)

        return {
            'name': _('Save XML'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'target': 'new',
            'view_id': result_view.id,
            'type': 'ir.actions.act_window',
        }

    def _move_lines_act_window(self):
        mod = 'account_move_line_search_extension'
        act = 'account_move_line_action_search_extension'
        act_window = self.env.ref(
            '%s.%s' % (mod, act),
            raise_if_not_found=False)
        if not act_window:
            mod_std = 'account'
            act_std = 'action_account_moves_all_a'
            act_window = self.env.ref('%s.%s' % (mod_std, act_std))
        return act_window.read()[0]
