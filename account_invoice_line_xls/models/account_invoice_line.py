# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_number = fields.Char(
        related='invoice_id.number', string='Invoice Number', readonly=True)
    invoice_type = fields.Selection(
        related='invoice_id.type', string='Invoice Type', readonly=True)
    invoice_state = fields.Selection(
        related='invoice_id.state', string='Invoice State', readonly=True)
    invoice_date = fields.Date(
        related='invoice_id.date_invoice', string='Invoice Date',
        readonly=True)
    invoice_journal_id = fields.Many2one(
        related='invoice_id.journal_id', string='Journal', readonly=True)

    @api.model
    def _report_xls_fields(self):
        """
        Adapt list in custom module to add/drop columns or change order.
        """
        return [
            'invoice_number', 'invoice_type', 'invoice_state',
            'journal', 'partner', 'date', 'account', 'description',
            'product', 'quantity', 'price_unit', 'discount',
            'price_subtotal', 'analytic_account',
            # 'partner_ref', 'product_ref', 'product_uos'
        ]

    @api.model
    def _report_xls_template(self):
        """
        Template updates, e.g.

        tmpl_upd = super(AccountInvoiceLine, self)._report_xls_template()
        tmpl_upd.update({
            'note': {
                'header': [1, 42, 'text', _render("_('Notes')")],
                'lines': [1, 0, 'text', _render("line.note or ''")],
                'totals': [1, 0, 'text', None]},
        }
        return tmpl_upd
        """
        return {}
