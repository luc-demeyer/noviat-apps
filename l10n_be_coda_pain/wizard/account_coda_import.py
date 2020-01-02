# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.exceptions import UserError

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
                if len(paylines) == 1 and paylines.move_line_id:
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
                raise UserError(_('Error!'), err_string)

        return reconcile_note

    def _match_payment_line(self, st_line, cba, transaction, payline,
                            reconcile_note):
        """
        Remark:
        We do not check on matching amounts in the case of a payment order
        with transfer account.
        The following process takes place when we have multiple journal items
        in a payment order reconciled against the transfer account:
        Partial reconciles while processing the statement lines until the
        last statement line corresponding to the payment order has been
        processed. This one results in a full reconcile. We could optimise
        this code by adding logic so that we reconcile only this last entry.
        """
        match = transaction['matching_info']
        match['status'] = 'done'
        match['partner_id'] = payline.partner_id.id
        amt_paid = transaction['amount']
        aml = payline.move_line_id
        cur = cba.currency_id
        payline_cur = payline.currency_id
        amt_fld = False
        if cur == payline_cur:
            if cur == cba.company_id.currency_id:
                amt_fld = 'amount_residual'
            else:
                amt_fld = 'amount_residual_currency'
        else:
            pass  # TODO: add extra multi-currency logic
        if aml.reconciled:
            payment_mode = payline.order_id.payment_mode_id
            transfer_account = payment_mode.transfer_account_id

            def aml_filter(l):
                return l.account_id == transfer_account

            if transfer_account and amt_fld:
                rec_amls = aml.full_reconcile_id.reconciled_line_ids
                cp_aml = rec_amls - aml
                transfer_aml = cp_aml.move_id.line_ids.filtered(
                    aml_filter)
                match['counterpart_amls'] = [(transfer_aml, amt_paid)]
        elif amt_fld and cur.is_zero(
                amt_paid - getattr(aml, amt_fld)):
            match['counterpart_amls'] = [(aml, amt_paid)]

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
