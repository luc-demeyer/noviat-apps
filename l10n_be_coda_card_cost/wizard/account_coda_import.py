# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _coda_statement_init_hook(self, coda_statement):
        """
        Define the matching keys in the coda_transaction_dict
        that for the lines which are candidates for a split.
        Extend the self._split_signatures dicts in a custom module
        if you want to refine the matching logic.
        Any field that is present in the 'coda_transaction_dist' can be used.
        """
        super(AccountCodaImport, self)._coda_statement_init_hook(
            coda_statement)
        cba = coda_statement['coda_bank_params']
        self._split_signatures = []
        split_rules = cba.account_mapping_ids.filtered(lambda r: r.split)
        for rule in split_rules:
            signature_dict = {
                'trans_type_id': rule.trans_type_id.id,
                'trans_family_id': rule.trans_family_id.id,
                'trans_code_id': rule.trans_code_id.id,
                'trans_category_id': rule.trans_category_id.id,
                'partner_name': rule.partner_name,
                'counterparty_number': rule.counterparty_number,
            }
            self._split_signatures.append((rule, signature_dict))

    def _coda_transaction_hook(self, coda_statement, transaction):
        """
        Remark:
        we could go a step further here and link the two resulting
        transaction together via a globalisation_id
        """
        for rule, sig in self._split_signatures:
            if sig.items() <= transaction.items():
                amount = self._coda_transaction_split_get_amount(
                    coda_statement, transaction,
                    rule.transaction_amount_pos)
                cost = self._coda_transaction_split_get_amount(
                    coda_statement, transaction,
                    rule.transaction_cost_pos)
                if amount and cost:
                    tr1 = transaction.copy()
                    tr1['amount'] = amount
                    ref_detail = int(transaction['ref_move_detail']) + 1
                    tr1['ref_move_detail'] = str(ref_detail).rjust(4, '0')
                    tr1['ref'] = tr1['ref_move'] + tr1['ref_move_detail']
                    tr2 = transaction.copy()
                    tr2['amount'] = -cost
                    ref_detail += 1
                    tr2['ref_move_detail'] = str(ref_detail).rjust(4, '0')
                    tr2['ref'] = tr2['ref_move'] + tr2['ref_move_detail']
                    if rule.cost_trans_code_id:
                        tr2['trans_code'] = rule.cost_trans_code_id.code
                        tr2['trans_code_id'] = rule.cost_trans_code_id.id
                        tr2['trans_code_desc'] = \
                            rule.cost_trans_code_id.description
                    if rule.cost_trans_category_id:
                        tr2['trans_category'] = \
                            rule.cost_trans_category_id.category
                        tr2['trans_category_id'] = \
                            rule.cost_trans_category_id.id
                        tr2['trans_category_desc'] = \
                            rule.cost_trans_category_id.description
                    self._format_transaction_note(coda_statement, tr2)
                    return [tr1, tr2]
        return [transaction]

    def _coda_transaction_split_get_amount(
            self, coda_statement, transaction, pos):

        cba = coda_statement['coda_bank_params']
        err_string = _(
            "\nIncorrect Amount/Cost Position defined "
            "in the 'split' mapping rule(s) of "
            "CODA Bank Account Configuration '%s'"
        ) % cba.name

        pos = pos and pos.split(',') or []
        if len(pos) != 2:
            self._coda_import_note += '\n' + err_string
            return False
        amount_prefix = pos[0]

        try:
            amount_len = int(pos[1])
        except Exception:
            self._coda_import_note += '\n' + err_string
            return False

        comm = transaction['communication'] or ''
        comm = comm.split(amount_prefix)
        amount = False
        if len(comm) == 2:
            amount = comm[1][:amount_len]
            amount = amount.replace(',', '.')
            try:
                amount = float(amount)
            except Exception:
                err_string = _(
                    "\nAmount conversion failure while processing "
                    "the 'split' mapping rule(s) of "
                    "CODA Bank Account Configuration '%s' "
                    "for transaction '%s'."
                ) % (cba.name, transaction['ref'])
                self._coda_import_note += '\n' + err_string
        else:
            err_string = _(
                "\nAmount detection failure while processing "
                "the 'split' mapping rule(s) of "
                "CODA Bank Account Configuration '%s' "
                "for transaction '%s'."
            ) % (cba.name, transaction['ref'])
            self._coda_import_note += '\n' + err_string

        return amount
