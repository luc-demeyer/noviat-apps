# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    percent_cd = fields.Float(
        string='Cash Discount (%)',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Add Cash Discount according to Belgian Tax Legislation.")
    amount_cd = fields.Monetary(
        string='Cash Discount',
        compute='_amount_cd',
        help="Total amount to pay with Cash Discount")
    date_cd = fields.Date(
        string='Cash Discount Date',
        help="Due Date for Cash Discount Conditions")
    country_code = fields.Char(
        related='company_id.country_id.code', readonly=True)

    @api.multi
    @api.depends('amount_total', 'amount_tax')
    def _amount_cd(self):
        for inv in self:
            if inv.company_id.country_id.code == 'BE':
                pct = inv.percent_cd
                if pct:
                    inv.amount_cd = inv.amount_untaxed * (1 - pct/100) \
                        + inv.amount_tax

    @api.onchange('percent_cd')
    def _onchange_percent_cd(self):
        """
        Recalc invoice line taxes.
        """
        self._onchange_invoice_line_ids()

    @api.onchange('payment_term_id', 'date_invoice')
    def _onchange_payment_term_date_invoice(self):
        super(AccountInvoice, self)._onchange_payment_term_date_invoice()
        self.date_cd = False

    @api.multi
    def action_date_assign(self):
        super(AccountInvoice, self).action_date_assign()
        for inv in self:
            if inv.type == 'out_invoice' and inv.percent_cd:
                if not inv.date_cd:
                    term_cd = inv.company_id.out_inv_cd_term
                    if inv.date_invoice:
                        date_invoice = inv.date_invoice
                    else:
                        date_invoice = time.strftime('%Y-%m-%d')
                    date_invoice = datetime.strptime(
                        date_invoice, '%Y-%m-%d').date()
                    date_cd = date_invoice + timedelta(term_cd)
                    inv.date_cd = date_cd.isoformat()
        return True

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        for invoice in self:
            pct = invoice.percent_cd
            if pct and invoice.company_id.country_id.code == 'BE':
                if invoice.currency_id != self.env.ref('base.EUR'):
                    raise UserError(_(
                        "The use of the belgian cash discount "
                        "is only allowed for belgian invoices in EUR."))
                if invoice.type in ['out_invoice', 'out_refund']:
                    cd_account = invoice.company_id.out_inv_cd_account_id
                else:
                    cd_account = invoice.company_id.in_inv_cd_account_id
                if not cd_account:
                    raise UserError(_(
                        "No account defined for the belgian cash discount."))
                multiplier = 1 - pct / 100
                cd_line = False
                cd_vals = {
                    'name': _('Cash Discount'),
                    'account_id': cd_account.id,
                    'partner_id': invoice.partner_id.id,
                    'currency_id': False,  # only EUR
                }
                cc_round = invoice.company_id.currency_id.round
                amount_cd = 0.0
                for line in move_lines:
                    vals = line[2]
                    if vals.get('tax_ids'):
                        cd_line = True
                        if vals.get('debit'):
                            debit = cc_round(vals['debit'])
                            vals['debit'] = cc_round(debit * multiplier)
                            amount_cd += debit - vals['debit']
                        if vals.get('credit'):
                            credit = cc_round(vals['credit'])
                            vals['credit'] = cc_round(credit * multiplier)
                            amount_cd -= credit - vals['credit']
                if cd_line:
                    if amount_cd > 0:
                        cd_vals['debit'] = amount_cd
                    else:
                        cd_vals['credit'] = -amount_cd
                    move_lines.append((0, 0, cd_vals))
        return move_lines

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None,
                        date=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        res['percent_cd'] = self.percent_cd
        return res

    @api.multi
    def get_taxes_values(self):
        self.ensure_one()
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        if self.company_id.country_id.code == 'BE':
            pct = self.percent_cd
            if pct:
                cc_round = self.company_id.currency_id.round
                multiplier = 1 - pct / 100
                for key in tax_grouped.keys():
                    tax_grouped[key].update({
                        'base': cc_round(
                            multiplier * tax_grouped[key]['base']),
                        'amount': multiplier * tax_grouped[key]['amount'],
                        })
        return tax_grouped
