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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp import api, fields, models

_logger = logging.getLogger(__name__)

BaseTaxCodesIn = ['81', '82', '83', '84', '85', '86', '87', '88']
BaseTaxCodesOut = ['00', '01', '02', '03', '44', '45', '46', '46L', '46T',
                   '47', '48', '48s44', '48s46L', '48s46T', '49']
BaseTaxCodes = BaseTaxCodesIn + BaseTaxCodesOut


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    # change compute method according to belgian regulation for Cash Discount
    @api.v8
    def compute(self, invoice):
        tax_grouped = super(AccountInvoiceTax, self).compute(invoice)
        # _logger.warn('tax_grouped=%s', tax_grouped)
        if invoice.company_id.country_id.code == 'BE':
            tax_codes = self.env['account.tax.code'].search(
                [('code', 'in', BaseTaxCodes)])
            atc_ids = [x.id for x in tax_codes]
            pct = invoice.percent_cd
            if pct:
                currency = invoice.currency_id.with_context(
                    date=invoice.date_invoice
                    or fields.Date.context_today(invoice))
                multiplier = 1 - pct / 100
                for k in tax_grouped.keys():
                    if k[1] in atc_ids:
                        tax_grouped[k].update({
                            'base': currency.round(
                                multiplier * tax_grouped[k]['base']),
                            'amount': multiplier * tax_grouped[k]['amount'],
                            'base_amount':
                                multiplier * tax_grouped[k]['base_amount'],
                            'tax_amount':
                                multiplier * tax_grouped[k]['tax_amount'],
                            })
        return tax_grouped
