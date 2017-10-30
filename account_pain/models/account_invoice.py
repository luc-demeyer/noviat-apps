# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    supplier_direct_debit = fields.Boolean(
        string='Supplier Direct Debit',
        help="Set this flag to exclude Supplier Invoices from the "
             "Payment Order 'Select Invoices to Pay' selection.")

    @api.onchange('supplier_invoice_number')
    def onchange_supplier_invoice_number(self):
        if self.reference_type == 'none' and self.type == 'in_invoice':
            self.reference = self.supplier_invoice_number

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        result = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice, payment_term, partner_bank_id,
            company_id)
        if type == 'in_invoice' and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            result['value']['supplier_direct_debit'] = \
                partner.supplier_direct_debit
        return result
