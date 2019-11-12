# Copyright 2009-2019 Noviat.
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

    def _check_duplicate_supplier_reference(self):
        """
        Replace the standard addons _check_duplicate_supplier_reference
        since this one is too restrictive (blocking) for certain use cases.
        """
        for invoice in self:
            if invoice.type in ('in_invoice', 'in_refund') \
                    and not invoice.force_encoding:
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
        Extra search term to detect duplicates in case no
        supplier_invoice_number has been specified.
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
        if self.supplier_invoice_number:
            dom_dups = domain + [
                ('supplier_invoice_number', 'ilike',
                 self.supplier_invoice_number)]
        else:
            dom_dups = domain + self._get_dup_domain_extra()
        return self.search(dom_dups)

    def _check_si_duplicate(self):
        dups = self._get_dup()
        if dups:
            raise UserError(_(
                "This Supplier Invoice has already been encoded !"
                "\nDuplicate Invoice: %s")
                % ', '.join([x.number for x in dups]))
