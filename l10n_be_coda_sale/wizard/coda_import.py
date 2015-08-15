# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _get_sale_order(self, coda_statement, line, coda_parsing_note):
        """
        check matching Sales Order number in free form communication
        """
        cba = coda_statement['coda_bank_params']
        free_comm = repl_special(line['communication'].strip())
        select = \
            "SELECT id FROM (SELECT id, name, '%s'::text AS free_comm, " \
            "regexp_replace(name, '[0]{3,10}', '0%%0') AS name_match " \
            "FROM sale_order WHERE state not in ('cancel', 'done') " \
            "AND company_id = %s) sq " \
            "WHERE free_comm ILIKE '%%'||name_match||'%%'" \
            % (free_comm, cba.company_id.id)
        self._cr.execute(select)
        res = self._cr.fetchall()
        return coda_parsing_note, res

    def _match_sale_order(self, coda_statement, line, coda_parsing_note):

        cba = coda_statement['coda_bank_params']
        match = {}

        if line['communication'] and cba.find_so_number \
                and line['amount'] > 0:
            so_res = self._get_sale_order(
                coda_statement, line, coda_parsing_note)
            if so_res and len(so_res) == 1:
                so_id = so_res[0][0]
                match['sale_order_id'] = so_id
                sale_order = self.env['sale.order'].browse(so_id)
                partner = sale_order.partner_id.commercial_partner_id
                line['partner_id'] = partner.id
                inv_ids = [x.id for x in sale_order.invoice_ids]
                if inv_ids:
                    amount_fmt = '%.2f'
                    if line['amount'] > 0:
                        amount_rounded = amount_fmt % round(line['amount'], 2)
                    else:
                        amount_rounded = amount_fmt \
                            % round(-line['amount'], 2)
                    self._cr.execute(
                        "SELECT id FROM account_invoice "
                        "WHERE state = 'open' AND amount_total = %s "
                        "AND id in %s",
                        (amount_rounded, tuple(inv_ids)))
                    res = self._cr.fetchall()
                    if res:
                        inv_ids = [x[0] for x in res]
                        if len(inv_ids) == 1:
                            invoice = self.env['account.invoice'].browse(
                                inv_ids[0])
                            imls = self.env['account.move.line'].search(
                                [('move_id', '=', invoice.move_id.id),
                                 ('reconcile_id', '=', False),
                                 ('account_id', '=', invoice.account_id.id)])
                            if imls:
                                line['reconcile'] = imls[0].id

        return coda_parsing_note, match


def repl_special(s):
    s = s.replace("\'", "\'" + "'")
    return s
