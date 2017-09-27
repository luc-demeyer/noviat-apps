# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    force_encoding = fields.Boolean(
        string='Force Encoding',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Accept the encoding of this invoice although "
             "it looks like a duplicate.")

    def _get_dup_domain(self):
        """
        override this method to customize customer specific
        duplicate check query
        """
        return [
            ('type', '=', self.type),
            ('commercial_partner_id', '=', self.commercial_partner_id.id),
            ('date_invoice', '=', self.date_invoice),
            ('amount_total', '=', self.amount_total),
            ('state', 'in', ['open', 'paid']),
            ('id', '!=', self.id)]

    def _get_dup(self):
        """
        override this method to customize customer specific
        duplicate check logic
        """
        # find duplicates by date, amount
        domain = self._get_dup_domain()
        dups1 = self.search(domain)
        # check supplier invoice number
        si = self.supplier_invoice_number \
            and self.supplier_invoice_number.lower()
        dups2 = self.env['account.invoice']
        for dup in dups1:
            dup_si = dup.supplier_invoice_number \
                and dup.supplier_invoice_number.lower()
            if si == dup_si:
                dups2 += dup
            if not si or not dup_si:
                dups2 += dup
            if si != dup_si:
                continue
        return dups2

    @api.one
    @api.constrains('state')
    def _check_si_duplicate(self):
        if self.type == 'in_invoice' and not self.force_encoding \
                and self.state not in ['draft', 'cancel']:
            dups = self._get_dup()
            if dups:
                raise Warning(_(
                    "This Supplier Invoice has already been encoded !"
                    "\nDuplicate Invoice: %s")
                    % ', '.join([x.internal_number
                                 for x in dups]))
