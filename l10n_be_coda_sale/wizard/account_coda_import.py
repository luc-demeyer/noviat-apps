# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _get_sale_order(self, st_line, cba, transaction, reconcile_note):
        """
        check matching Sales Order number in free form communication
        """
        free_comm = repl_special(transaction['communication'].strip())
        select = (
            "SELECT id FROM (SELECT id, name, '%s'::text AS free_comm, "
            "regexp_replace(name, '[0]{3,10}', '0%%0') AS name_match "
            "FROM sale_order WHERE state not in ('cancel', 'done') "
            "AND company_id = %s) sq "
            "WHERE free_comm ILIKE '%%'||name_match||'%%'"
            ) % (free_comm, cba.company_id.id)
        self.env.cr.execute(select)
        res = self.env.cr.fetchall()
        return reconcile_note, res

    def _match_sale_order(self, st_line, cba, transaction, reconcile_note):
        """
        TODO: refactor code to remove cr.execute, invoice rebrowse, search
        """

        match = transaction['matching_info']

        if match['status'] in ['break', 'done']:
            return reconcile_note

        if transaction['communication'] and cba.find_so_number \
                and transaction['amount'] > 0:
            reconcile_note, so_res = self._get_sale_order(
                st_line, cba, transaction, reconcile_note)
            if so_res and len(so_res) == 1:
                so_id = so_res[0][0]
                match['status'] = 'done'
                match['sale_order_id'] = so_id
                sale_order = self.env['sale.order'].browse(so_id)
                partner = sale_order.partner_id.commercial_partner_id
                match['partner_id'] = partner.id
                inv_ids = [x.id for x in sale_order.invoice_ids]
                if inv_ids:
                    amount_fmt = '%.2f'
                    if transaction['amount'] > 0:
                        amount_rounded = \
                            amount_fmt % round(transaction['amount'], 2)
                    else:
                        amount_rounded = amount_fmt \
                            % round(-transaction['amount'], 2)
                    self.env.cr.execute(
                        "SELECT id FROM account_invoice "
                        "WHERE state = 'open' "
                        "AND round(amount_total, 2) = %s "
                        "AND id in %s",
                        (amount_rounded, tuple(inv_ids)))
                    res = self.env.cr.fetchall()
                    if res:
                        inv_ids = [x[0] for x in res]
                        if len(inv_ids) == 1:
                            invoice = self.env['account.invoice'].browse(
                                inv_ids)
                            imls = self.env['account.move.line'].search(
                                [('move_id', '=', invoice.move_id.id),
                                 ('reconcile_id', '=', False),
                                 ('account_id', '=', invoice.account_id.id)])
                            if imls:
                                cur = cba.currency_id
                                cpy_cur = cba.company_id.currency_id
                                # TODO: add support for more
                                # multi-currency use cases
                                if invoice.currency_id == cur:
                                    if cur == cpy_cur:
                                        amt_fld = 'amount_residual'
                                    else:
                                        amt_fld = 'amount_residual_currency'
                                    match['counterpart_amls'] = [
                                        (aml, getattr(aml, amt_fld))
                                        for aml in imls]

        return reconcile_note


def repl_special(s):
    s = s.replace("\'", "\'" + "'")
    return s
