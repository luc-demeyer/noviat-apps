# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, _
from openerp.exceptions import Warning


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _match_payment_reference(self, st_line, cba, transaction,
                                 reconcile_note):
        """
        check payment reference in bank statement line
        against payment order lines
        """
        payment_reference = transaction['payment_reference']
        match = {}

        if payment_reference and cba.find_payment \
                and transaction['amount'] < 0:
            paylines = self.env['payment.line'].search(
                [('name', '=', payment_reference)])
            if paylines:
                if len(paylines) == 1:
                    payline = paylines[0]
                    match['payment_line_id'] = payline.id
                    transaction['payment_line_id'] = payline.id
                    transaction['partner_id'] = payline.partner_id.id
                    if payline.move_line_id:
                        transaction['reconcile_id'] = payline.move_line_id.id
                else:
                    err_string = _(
                        "\nThe CODA parsing detected a "
                        "payment reference ambiguity while processing "
                        "movement data record 2.3, ref %s!"
                        "\nPlease check your Payment Gateway configuration "
                        "or contact your Odoo support channel."
                        ) % transaction['ref']
                    raise Warning(_('Error!'), err_string)

        return reconcile_note, match
