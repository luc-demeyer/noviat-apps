# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import fields, _
from openerp.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)


class CommonAccrual(object):

    def _prepare_accrual_move_ref(self):
        return self.name

    def _prepare_accrual_move_vals(self, aml_vals, journal_id):
        if not journal_id:
            journal_id = self.company_id.accrual_journal_id.id
        if not journal_id:
            msg = _("No Accruals Journal defined.")
            action = self.env.ref('base.action_res_company_form')
            raise RedirectWarning(
                msg, action.id,
                _('Go to company configuration screen'))
        ref = self._prepare_accrual_move_ref()
        move_vals = {
            'ref': ref,
            'journal_id': journal_id,
            'date': fields.Date.today(),
            'company_id': self.company_id.id,
        }
        return move_vals

    def _accrual_hashcode_fields(self, entry):
        return {
            'product_id': entry.get('product_id') or False,
            'account_id': entry['account_id'] or False,
            'entry_type': entry['entry_type'],
        }

    def _accrual_hashcode(self, entry):
        hc_fields = self._accrual_hashcode_fields(entry)
        hashcode = '-'.join([unicode(f) for f in hc_fields.itervalues()])
        return hashcode

    def _accrual_fields_to_sum(self):
        return ['debit', 'credit', 'quantity']

    def _update_accrual_move_line_vals(self, entry):
        """
        Placeholder for customizations
        """
        pass

    def _create_accrual_move(self, aml_vals, journal_id=False):
        accrual_move_id = self.env['account.move'].create(
            self._prepare_accrual_move_vals(aml_vals, journal_id))

        grouped = {}
        fields_to_sum = self._accrual_fields_to_sum()
        for entry in aml_vals:
            hashcode = self._accrual_hashcode(entry)
            if hashcode in grouped:
                for field in entry:
                    if field in fields_to_sum:
                        grouped[hashcode][field] += entry[field]
            else:
                grouped[hashcode] = entry

        accruals = {}
        for group in grouped:
            entry = grouped[group]
            entry_type = entry['entry_type']
            del entry['entry_type']
            entry['move_id'] = accrual_move_id.id
            self._update_accrual_move_line_vals(entry)
            aml = self.env['account.move.line'].create(entry)
            if entry_type == 'accrual':
                accruals[entry.get('product_id')] = aml

        return accrual_move_id.id, accruals

    def _reconcile_accrued_expense_lines(self, accrual_lines):
        """
        The 'to_correct' dict is returned so that extension
        modules can take specific actions on these entries
        such as the creation of a correction booking to enable
        automatic reconciliation.
        In a generic module this is not possible because a
        failing reconcile could be perfectly valid (e.g.
        a single Sales Invoice linked to multiple Purchase Orders
        will give failing reconciles until the last PO is approved).
        """
        to_correct = {}
        for p_id in accrual_lines:
            to_reconcile = accrual_lines[p_id]
            if len(to_reconcile) < 2:
                _logger.error(_(
                    "%s, accrual reconcile failed for "
                    "account.move.line ids %s, "
                    "len(to_reconcile) < 2"),
                    self.name, [x.id for x in to_reconcile]
                )
                continue
            if to_reconcile.mapped('reconcile_id'):
                rec_refs = to_reconcile.mapped('reconcile_id').mapped('name')
                _logger.error(_(
                    "%s, accrual reconcile failed for "
                    "account.move.line ids %s, "
                    "some entries are already reconciled, "
                    "cf. reconcile refs %s"),
                    self.name, [x.id for x in to_reconcile],
                    rec_refs)
                continue
            check = check_cur = 0.0
            currencies = self.env['res.currency']
            for l in to_reconcile:
                if l.currency_id:
                    currencies |= l.currency_id
                    check_cur += l.amount_currency
                check += l.debit - l.credit
            if len(currencies) > 1:
                to_correct[p_id] = (accrual_lines[p_id], check)
                _logger.error(_(
                    "%s, accrual reconcile failed for "
                    "account.move.line ids %s, "
                    "foreign currencies inconsistent"),
                    self.name, [x.id for x in to_reconcile]
                )
            elif len(currencies) == 1:
                if currencies.is_zero(check_cur):
                    ctx = dict(self._context,
                               account_period_prefer_normal=True)
                    period = self.env[
                        'account.period'].with_context(ctx).find()
                    to_reconcile.reconcile(
                        writeoff_journal_id=to_reconcile[0].journal_id.id,
                        writeoff_period_id=period.id)
                else:
                    to_correct[p_id] = (accrual_lines[p_id], check)
                    _logger.error(_(
                        "%s, accrual reconcile failed for "
                        "account.move.line ids %s, "
                        "sum(amount_currency != 0.0"),
                        self.name, [x.id for x in to_reconcile]
                    )
            elif self.company_id.currency_id.is_zero(check):
                to_reconcile.reconcile()
            else:
                to_correct[p_id] = (accrual_lines[p_id], check)
                _logger.error(_(
                    "%s, accrual reconcile failed for "
                    "account.move.line ids %s, "
                    "sum(debit) != sum(credit)"),
                    self.name, [x.id for x in to_reconcile]
                )
        return to_correct
