# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # payterm_keep, duedate_keep:
    # hidden Fields to avoid removal of Payment Terms
    # when Due Date is modified as a consequence of Payment Term Calculation.
    payterm_keep = fields.Boolean(string='Keep Payment Terms')
    duedate_keep = fields.Boolean(string='Keep Payment Terms')

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        if not self.duedate_keep:
            super(AccountInvoice, self)._onchange_payment_term_date_invoice()
        self.payterm_keep = True

    @api.onchange('date_due')
    def _onchange_date_due(self):
        """
        Remove payment term when changing the due date manually
        since otherwise the invoice 'validate' will recalculate
        the due date and hence overwrite the manual change.
        """
        if self.date_due and not self.payterm_keep:
            self.payment_term_id = False
            self.duedate_keep = True
        self.payterm_keep = False
