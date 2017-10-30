# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from lxml import etree
import logging

from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    duedate = fields.Date(default=lambda self: self._default_duedate())

    @api.model
    def _default_duedate(self):
        return (date.today() + timedelta(30)).isoformat()

    def journal_domain(self):
        """
        Use this method to customize the journals to search on.
        By default we exclude financial journals to filter out
        unreconciled advanced payments from customers.
        """
        journal_domain = [
            ('journal_id.type', 'in',
             ['purchase', 'sale_refund', 'general', 'situation'])]
        return journal_domain

    @api.multi
    def search_entries(self):
        """
        Fix line_ids query
        """
        res = super(PaymentOrderCreate, self).search_entries()
        # Search for move line to pay:
        domain = [('reconcile_id', '=', False),
                  ('partner_id', '!=', False),
                  ('move_id.state', '=', 'posted'),
                  ('account_id.type', 'in', ['payable', 'receivable']),
                  ('amount_to_pay', '>', 0)]
        domain += ['|',
                   ('date_maturity', '<=', self.duedate),
                   ('date_maturity', '=', False)]
        journal_domain = self.journal_domain()
        domain += journal_domain
        amls = self.env['account.move.line'].search(domain)
        amls = amls.filtered(lambda r: not r.invoice.supplier_direct_debit)
        res['context'].update({'line_ids': amls.ids})
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """
        add context to 'entries' field for use in account.move.line
        """
        res = super(PaymentOrderCreate, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if 'line_ids' in self._context and view_type == 'form':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='entries']")
            for node in nodes:
                node.set('context',
                         "{'account_payment':'1', 'view_mode':'tree'}")
                node.set('colspan', '4')
                node.set('height', '300')
                node.set('width', '800')
            res['arch'] = etree.tostring(doc)
        return res

    def _prepare_payline_vals(self, payment, aml, line2bank):
        company_currency = payment.mode.company_id.currency_id
        if payment.date_prefered == "now":
            # no payment date => immediate payment
            date_to_pay = False
        elif payment.date_prefered == 'due':
            date_to_pay = aml.date_maturity
        elif payment.date_prefered == 'fixed':
            date_to_pay = payment.date_scheduled
        partner_id = aml.partner_id \
            and aml.partner_id.id or False
        pl_vals = {
            'move_line_id': aml.id,
            'amount_currency': aml.amount_to_pay,
            'bank_id': line2bank.get(aml.id),
            'order_id': payment.id,
            'partner_id': partner_id,
            'communication': aml.ref or '/',
            'date': date_to_pay,
            'currency': aml.currency_id.id or company_currency.id,
        }
        return pl_vals

    @api.multi
    def create_payment(self):
        """
        Replacement (without super !) of the original one
        for multi-currency purposes
        """
        if not self.entries:
            return {'type': 'ir.actions.act_window_close'}

        payment = self.env['payment.order'].browse(self._context['active_id'])
        line2bank = self.entries.line2bank(payment.mode.id)
        for aml in self.entries:
            payline_vals = self._prepare_payline_vals(payment, aml, line2bank)
            self.env['payment.line'].create(payline_vals)
        return {'type': 'ir.actions.act_window_close'}
