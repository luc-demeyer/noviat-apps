# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields, api, _


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    force_encoding = fields.Boolean(
        string='Force Encoding',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Accept the encoding of this invoice although "
             "it looks like a duplicate.")

    def _get_dup_domain(self):
        """
        override this method to customise customer specific
        duplicate check query
        """
        return [
            ('type', '=', self.type),
            ('partner_id', '=', self.partner_id.id),
            ('date_invoice', '=', self.date_invoice),
            ('amount_total', '=', self.amount_total),
            ('state', 'in', ['open', 'paid']),
            ('id', '!=', self.id)]

    def _get_dup(self):
        """
        override this method to customise customer specific
        duplicate check logic
        """
        # find duplicates by date, amount
        domain = self._get_dup_domain()
        dups = self.search(domain)
        # check supplier invoice number
        if dups:
            if self.supplier_invoice_number:
                for dup in dups:
                    if not dup.supplier_invoice_number \
                        or dup.supplier_invoice_number.lower() == \
                            self.supplier_invoice_number.lower():
                        return dup
                    return False
            return dups[0]
        return False

    @api.one
    @api.constrains('state')
    def _check_si_duplicate(self):
        if self.type == 'in_invoice' and not self.force_encoding \
                and self.state not in ['draft', 'cancel']:
            dup = self._get_dup()
            if dup:
                raise Warning(_(
                    "This Supplier Invoice has already been encoded !"
                    "\nDuplicate Invoice: %s")
                    % dup.internal_number)
