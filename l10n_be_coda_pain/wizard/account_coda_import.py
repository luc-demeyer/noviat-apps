# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# TODO: Add more keys (direct debit, international credit transfers, ...)
_TRANSACTION_KEYS = [('0', '01', '01', '000')]


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _match_payment_reference(self, st_line, cba, transaction,
                                 reconcile_note):
        """
        Check payment reference in bank statement line
        against payment order lines.
        """
        match = transaction['matching_info']

        if match['status'] in ['break', 'done']:
            return reconcile_note
        if self._skip_payment_reference_match(
                st_line, cba, transaction, reconcile_note):
            return reconcile_note

        bankpaylines = self.env['bank.payment.line'].search(
            [('name', '=', transaction['payment_reference'])])
        if bankpaylines:
            if len(bankpaylines) == 1:
                # we do not use the 'bank_payment_line_id' entry
                # in the matching_info at this point in time but
                # we store it to facilitate bug fixing
                match['bank_payment_line_id'] = bankpaylines.id
                paylines = bankpaylines.payment_line_ids
                if paylines:
                    reconcile_note = self._match_payment_line(
                        st_line, cba, transaction, paylines, reconcile_note)
            else:
                err_string = _(
                    "\nThe CODA parsing detected a "
                    "payment reference ambiguity while processing "
                    "movement data record 2.3, ref %s!"
                    "\nPlease check your Payment Gateway configuration "
                    "or contact your Odoo support channel."
                    ) % transaction['ref']
                raise UserError(err_string)

        return reconcile_note

    def _match_payment_line(self, st_line, cba, transaction, paylines,
                            reconcile_note):
        """
        Remark:
        We do not check on matching amounts in the case of a payment order,
        hence reconciles can be partial.

        The following process takes place when multiple journal items in
        a payment order are reconciled against the transfer account:

        We may have multiple bank statements lines with the same counterpart
        journal item on the transfer account if the 'group_lines'
        option is not set.
        Partial reconciles are made while processing the statement lines until
        the last statement line corresponding to the payment order has been
        processed. This one results in a full reconcile of the transfer
        account journal item.
        """
        match = transaction['matching_info']
        match['status'] = 'done'
        match['partner_id'] = paylines[0].partner_id.id
        amt_paid = transaction['amount']
        payment_mode = paylines[0].order_id.payment_mode_id
        transfer_account = payment_mode.transfer_account_id
        transfer_journal = payment_mode.transfer_journal_id

        transfer_aml = self.env['account.move.line']
        counterpart_amls = []
        # Case 1: payment mode with group_lines=True
        if payment_mode.group_lines:
            # Case 1a: transfer_account
            if transfer_account:
                for payline in paylines:
                    aml = payline.move_line_id
                    rec_amls = aml.full_reconcile_id.reconciled_line_ids
                    cp_aml = rec_amls.filtered(
                        lambda r: r.journal_id == transfer_journal)
                    transfer_aml = cp_aml.move_id.line_ids.filtered(
                        lambda r: r.account_id == transfer_account)
                    if transfer_aml:
                        counterpart_amls += [(transfer_aml, amt_paid)]
                        break
            # Case 1b: no transfer_account
            else:
                for payline in paylines:
                    aml = payline.move_line_id
                    if (
                        aml.account_id.internal_type
                        not in ('receivable', 'payable')
                    ):
                        continue
                    amt_fld = False
                    if cba.currency_id == payline.currency_id:
                        if cba.currency_id == cba.company_id.currency_id:
                            amt_fld = 'amount_residual'
                        else:
                            amt_fld = 'amount_residual_currency'
                    else:
                        pass  # TODO: add extra multi-currency logic
                    if amt_fld:
                        counterpart_amls += [(aml, getattr(aml, amt_fld))]
        # Case 2: payment mode with group_lines=False
        # Remark len(paylines) == 1:
        # we do not support the use case where payment mode config has been
        # changed between upload of payment order and download of CODA file
        elif len(paylines) == 1:
            # Case 2a: transfer_account
            if transfer_account:
                aml = paylines.move_line_id
                rec_amls = aml.full_reconcile_id.reconciled_line_ids
                cp_aml = rec_amls - aml
                transfer_aml = cp_aml.move_id.line_ids.filtered(
                    lambda r: r.account_id == transfer_account)
                if transfer_aml:
                    counterpart_amls += [(transfer_aml, amt_paid)]
            # Case 2b: no transfer_account
            else:
                aml = paylines.move_line_id
                if (
                    aml.account_id.internal_type
                    in ('receivable', 'payable')
                ):
                    counterpart_amls += [(aml, amt_paid)]

        match['counterpart_amls'] = counterpart_amls
        return reconcile_note

    def _skip_payment_reference_match(self, st_line, cba, transaction,
                                      reconcile_note):
        skip = False
        if not transaction['payment_reference']:
            skip = True
        if not cba.find_payment:
            skip = True
        if transaction['amount'] >= 0.0:
            skip = True

        matching_key = False
        for k in _TRANSACTION_KEYS:
            if (k[0] == transaction['trans_type']
                    and k[1] == transaction['trans_family']
                    and k[2] == transaction['trans_code']
                    and k[3] == transaction['trans_category']):
                matching_key = True
                break
        if not matching_key:
            skip = True

        return skip
