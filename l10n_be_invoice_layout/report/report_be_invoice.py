# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from openerp.report import report_sxw
from openerp import models, _
from openerp.tools.translate import translate
from openerp.exceptions import except_orm


class be_invoice(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(be_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'format_vat': self._format_vat,
            'get_company_data': self._get_company_data,
            'get_partner_data': self._get_partner_data,
            'get_address': self._get_address,
            'tax_rates': self._tax_rates,
            'payment_methods': self._payment_methods,
            'bank_account': self._invoice_bank_account,
            'tax_lines': self._tax_lines,
            '_': self._,
        })
        itn = __name__.split('openerp.')[1]
        self._ir_translation_name = itn.replace('.', '/') + '.py'
        self.context = context

    def _(self, src, type='code'):
        lang = self.localcontext.get('lang', 'en_US')
        return translate(self.cr, self._ir_translation_name,
                         type, lang, src) or src

    def _format_vat(self, vat):
        vat = vat or ''
        vat = vat.replace(' ', '').upper()
        if vat[0:2] == 'BE':
            vat = vat[0:2] + ' ' + '.'.join([vat[2:6], vat[6:9], vat[9:12]])
        return vat

    def _get_company_data(self, invoice):
        cpy = invoice.company_id
        p = cpy.partner_id
        add_country = p.country_id != invoice.partner_id.country_id
        res = '<b>' + p.name
        if p.title:
            res += ' ' + p.title.name
        res += '</b><br/>' + self._get_address(p, add_country)
        if p.vat:
            res += '<br/>' + self._format_vat(p.vat)
        elif p.registry_number:
            res += '<br/>' + p.registry_number
        if cpy.company_registry:
            res += '<br/>' + cpy.company_registry
        return res

    def _get_partner_data(self, invoice):
        p = invoice.partner_id
        p_cpy = p.commercial_partner_id
        add_country = p.country_id != invoice.partner_id.country_id
        res = '<b>' + p_cpy.name
        if p_cpy.title:
            res += ' ' + p_cpy.title.name
        res += '</b>'
        if p.parent_id and not p.is_company:
            res += '<br/>' + self._("Attn.") + ' '
            if p.title:
                res += p.title.name + ' '
            res += p.name
        res += '<br/>' + self._get_address(p, add_country)
        return res

    def _get_address(self, p, add_country=False):
        res = ''
        p_be = p.country_id and p.country_id.code == 'BE'
        if p.street:
            res += p.street + '<br/>'
        if p.street2:
            res += p.street2 + '<br/>'
        if p.zip:
            cityline = (
                p_be and not add_country and ('B-' + p.zip) or p.zip) + ' '
        else:
            cityline = ''
        if p.city:
            cityline += p.city
        if cityline:
            res += cityline
        if p.country_id and (add_country or not p_be):
            res += '<br/>' + p.country_id.name
        return res

    def _tax_rates(self, taxes):
        if not taxes:
            return '0'
        tax_codes = [tax.description for tax in taxes]
        try:
            res = set(map(lambda x: x[1] == 'OUT' and x[2] or x[3],
                          [x.split('-') for x in tax_codes]))
            return ', '.join([x[0] == '0' and x[1] or x for x in res])
        except:
            return ', '.join([lt.name or '' for lt in taxes])

    def _tax_lines(self, tax_lines):
        """
        group tax lines per tax %
        """
        td = {}
        for tl in tax_lines:
            tax_amount = tl.tax_amount or 0.0
            base_amount = tl.base_amount or 0.0
            try:
                tax_rate = round((tax_amount/base_amount) * 100, 1)
            except:
                tax_rate = tl.name
            if 'tax_rate' not in td:
                td[tax_rate] = {
                    'base_amount': base_amount,
                    'tax_amount': tax_amount}
            else:
                td[tax_rate]['base_amount'] += base_amount
                td[tax_rate]['tax_amount'] += tax_amount
        res = []
        for k in sorted(td.iterkeys()):
            if isinstance(k, float):
                name = (k % 1 and '%.1f' or '%.f') % k + '%'
            else:
                name = k
            res.append((name, td[k]['base_amount'], td[k]['tax_amount']))
        return res

    def _payment_methods(self, invoice):
        payment_journals = [x.journal_id for x in invoice.payment_ids]
        payment_methods = ','.join([x.name for x in payment_journals])
        return payment_methods

    def _invoice_bank_account(self):
        """
        Returns the first bank account of the document footer.
        """
        company = self.localcontext['company']
        banks = company.bank_ids
        bank_account = False
        for bank in banks:
            if bank.footer:
                bank_account = bank.state == 'iban' and 'IBAN ' or ''
                bank_account += bank.acc_number
                return bank_account
        raise except_orm(
            _('Insufficient Data!'),
            _('No bank account defined for the Company footer.'))


class report_be_invoice(models.AbstractModel):
    _name = 'report.l10n_be_invoice_layout.report_be_invoice'
    _inherit = 'report.abstract_report'
    _template = 'l10n_be_invoice_layout.report_be_invoice'
    _wrapped_report_class = be_invoice
