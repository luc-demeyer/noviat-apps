# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.exceptions import UserError


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
        payment_reference = transaction['payment_reference']
        match = {}

        if payment_reference and cba.find_payment \
                and transaction['amount'] < 0:
            bankpaylines = self.env['bank.payment.line'].search(
                [('name', '=', payment_reference)])
            if bankpaylines:
                if len(bankpaylines) == 1:
                    match['bank_payment_line_id'] = bankpaylines.id
                    transaction['bank_payment_line_id'] = bankpaylines.id
                    transaction['partner_id'] = bankpaylines.partner_id.id
                    paylines = bankpaylines.payment_line_ids
                    if len(paylines) == 1 and paylines.move_line_id:
                        transaction['reconcile_id'] = paylines.move_line_id.id
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
