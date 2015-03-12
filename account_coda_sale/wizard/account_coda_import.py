# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from openerp.osv import orm
import logging
_logger = logging.getLogger(__name__)


class account_coda_import(orm.TransientModel):
    _inherit = 'account.coda.import'

    def _get_sale_order(self, cr, uid, st_line, coda_parsing_note, coda_statement, context=None):
        # check matching Sales Order number in free form communication
        free_comm = repl_special(st_line['communication'].strip())
        select = "SELECT id FROM (SELECT id, name, '%s'::text AS free_comm, regexp_replace(name, '[0]{3,10}', '0%%0') AS name_match " \
            "FROM sale_order WHERE state not in ('cancel', 'done') AND company_id = %s) sq " \
            "WHERE free_comm ILIKE '%%'||name_match||'%%'" \
            % (free_comm, coda_statement['company_id'])
        cr.execute(select)
        res = cr.fetchall()
        return res

    def _match_sale_order(self, cr, uid, st_line, coda_parsing_note, coda_statement, context=None):
        so_obj = self.pool.get('sale.order')
        inv_obj = self.pool.get('account.invoice')
        move_line_obj = self.pool.get('account.move.line')
        coda_bank_params = coda_statement['coda_bank_params']
        find_so_number = coda_bank_params['find_so_number']
        match={}

        if st_line['communication'] and find_so_number and st_line['amount'] > 0:
            so_res = self._get_sale_order(cr, uid, st_line, coda_parsing_note, coda_statement, context=None)
            if so_res and len(so_res) == 1:
                so_id = so_res[0][0]
                match['sale_order_id'] = so_id
                sale_order = so_obj.browse(cr, uid, so_id)
                partner = sale_order.partner_id
                st_line['partner_id'] = partner.id
                st_line['account_id'] = partner.property_account_receivable.id
                st_line['type'] = 'customer'
                inv_ids = [x.id for x in sale_order.invoice_ids]
                if inv_ids:
                    amount_fmt = '%.' + str(self.digits) + 'f'
                    if st_line['amount'] > 0:
                        amount_rounded = amount_fmt % round(st_line['amount'], self.digits)
                    else:
                        amount_rounded = amount_fmt % round(-st_line['amount'], self.digits)        
                    cr.execute("SELECT id FROM account_invoice " \
                        "WHERE state = 'open' AND amount_total = %s AND id in %s",
                        (amount_rounded, tuple(inv_ids)))
                    res = cr.fetchall()
                    if res:
                        inv_ids = [x[0] for x in res]
                        if len(inv_ids) == 1:
                            invoice = inv_obj.browse(cr, uid, inv_ids[0], context=context)
                            iml_ids = move_line_obj.search(cr, uid, [('move_id', '=', invoice.move_id.id), ('reconcile_id', '=', False), ('account_id.reconcile', '=', True)])
                            if iml_ids:
                                st_line['reconcile'] = iml_ids[0]                      

        #_logger.warn('%s, st_line=%s, match=%s', self._name, st_line, match)  # diagnostics
        return st_line, coda_parsing_note, match

def repl_special(s):
    s = s.replace("\'", "\'" + "'")
    return s

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: