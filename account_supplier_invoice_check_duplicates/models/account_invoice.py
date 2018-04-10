# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    force_encoding = fields.Boolean(
        string='Force Encoding',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Accept the encoding of this invoice although "
             "it looks like a duplicate.")

    def _check_invoice_reference(self):
        """
        Replace the standard addons _check_invoice_reference
        since this one is too restrict (blocking) for certain instances.
        """
        for invoice in self:
            if not invoice.force_encoding:
                invoice._check_si_duplicate()

    def _get_dup_domain(self):
        """
        Override this method to customize customer specific
        duplicate check query.
        """
        return [
            ('type', '=', self.type),
            ('commercial_partner_id', '=', self.commercial_partner_id.id),
            ('state', 'in', ['open', 'paid']),
            ('company_id', '=', self.company_id.id),
            ('id', '!=', self.id)]

    def _get_dup_domain_extra(self):
        """
        Extra search term to detect duplicates in case no reference
        has been specified.
        """
        return [('date_invoice', '=', self.date_invoice),
                ('amount_total', '=', self.amount_total)]

    def _get_dup(self):
        """
        Override this method to customize customer specific
        duplicate check logic
        """
        # find duplicates by date, amount
        domain = self._get_dup_domain()
        # add supplier invoice number
        if self.reference:
            dom_dups = domain + [('reference', 'ilike', self.reference)]
        else:
            dom_dups = domain + self._get_dup_domain_extra()
        return self.search(dom_dups)

    def _check_si_duplicate(self):
        if self.type in ['in_invoice', 'in_refund']:
            dups = self._get_dup()
            if dups:
                raise UserError(_(
                    "This Supplier Invoice has already been encoded !"
                    "\nDuplicate Invoice: %s")
                    % ', '.join([x.number for x in dups]))
