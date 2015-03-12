# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2010-now Noviat nv/sa (www.noviat.com).
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
import logging
_logger = logging.getLogger(__name__)


class account_coda_import(models.TransientModel):
    _inherit = 'account.coda.import'

    def _get_sale_order(self, cr, uid, coda_statement, line,
                        coda_parsing_note, context=None):
        """
        check matching Sales Order number in free form communication
        """
        free_comm = repl_special(line['communication'].strip())
        select = \
            "SELECT id FROM (SELECT id, name, '%s'::text AS free_comm, " \
            "regexp_replace(name, '[0]{3,10}', '0%%0') AS name_match " \
            "FROM sale_order WHERE state not in ('cancel', 'done') " \
            "AND company_id = %s) sq " \
            "WHERE free_comm ILIKE '%%'||name_match||'%%'" \
            % (free_comm, coda_statement['company_id'])
        cr.execute(select)
        res = cr.fetchall()
        return coda_parsing_note, res

    def _match_sale_order(self, cr, uid, coda_statement, line,
                          coda_parsing_note, context=None):

        so_obj = self.pool['sale.order']
        inv_obj = self.pool['account.invoice']
        aml_obj = self.pool['account.move.line']
        cba = coda_statement['coda_bank_params']
        find_so_number = cba['find_so_number']
        match = {}

        if line['communication'] and find_so_number \
                and line['amount'] > 0:
            so_res = self._get_sale_order(
                cr, uid, coda_statement, line, coda_parsing_note,
                context=context)
            if so_res and len(so_res) == 1:
                so_id = so_res[0][0]
                match['sale_order_id'] = so_id
                sale_order = so_obj.browse(cr, uid, so_id)
                partner = sale_order.partner_id
                line['partner_id'] = partner.id
                inv_ids = [x.id for x in sale_order.invoice_ids]
                if inv_ids:
                    amount_fmt = '%.2f'
                    if line['amount'] > 0:
                        amount_rounded = amount_fmt % round(line['amount'], 2)
                    else:
                        amount_rounded = amount_fmt \
                            % round(-line['amount'], 2)
                    cr.execute(
                        "SELECT id FROM account_invoice "
                        "WHERE state = 'open' AND amount_total = %s "
                        "AND id in %s",
                        (amount_rounded, tuple(inv_ids)))
                    res = cr.fetchall()
                    if res:
                        inv_ids = [x[0] for x in res]
                        if len(inv_ids) == 1:
                            invoice = inv_obj.browse(
                                cr, uid, inv_ids[0], context=context)
                            iml_ids = aml_obj.search(
                                cr, uid,
                                [('move_id', '=', invoice.move_id.id),
                                 ('reconcile_id', '=', False),
                                 ('account_id', '=', invoice.account_id.id)])
                            if iml_ids:
                                line['reconcile'] = iml_ids[0]

        return coda_parsing_note, match


def repl_special(s):
    s = s.replace("\'", "\'" + "'")
    return s
