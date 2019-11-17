# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.exceptions import UserError

# TODO: Add more keus (direct debit, international credit transfers, ...)
_TRANSACTION_KEYS = [('0', '01', '01', '000')]


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _match_payment_reference(self, st_line, cba, transaction,
                                 reconcile_note):
        """
        check payment reference in bank statement line
        against payment order lines
        TODO:
        Extend logic to support Transfer Accounts and grouped transactions.
        """
        match = {}

        if self._skip_payment_reference_match(
                st_line, cba, transaction, reconcile_note):
            return reconcile_note, match

        bankpaylines = self.env['bank.payment.line'].search(
            [('name', '=', transaction['payment_reference'])])
        if bankpaylines:
            if len(bankpaylines) == 1:
                match['bank_payment_line_id'] = bankpaylines.id
                transaction['bank_payment_line_id'] = bankpaylines.id
                transaction['partner_id'] = bankpaylines.partner_id.id
                paylines = bankpaylines.payment_line_ids
                if len(paylines) == 1 and paylines.move_line_id:
                    aml = paylines.move_line_id
                    cur = cba.currency_id
                    payline_cur = paylines.currency_id
                    amt_fld = False
                    if cur == payline_cur:
                        if cur == cba.company_id.currency_id:
                            amt_fld = 'amount_residual'
                        else:
                            amt_fld = 'amount_residual_currency'
                    else:
                        pass  # TODO: add extra multi-currency logic
                    if amt_fld and cur.is_zero(
                            transaction['amount'] - getattr(aml, amt_fld)):
                        transaction['counterpart_amls'] = [aml]
            else:
                err_string = _(
                    "\nThe CODA parsing detected a "
                    "payment reference ambiguity while processing "
                    "movement data record 2.3, ref %s!"
                    "\nPlease check your Payment Gateway configuration "
                    "or contact your Odoo support channel."
                    ) % transaction['ref']
                raise UserError(_('Error!'), err_string)

        return reconcile_note, match

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
