# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, _
from openerp.exceptions import Warning


class account_move_reconcile(models.Model):
    _inherit = 'account.move.reconcile'

    def reconcile_partial_check(self, cr, uid, ids, type='auto', context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            line_ids = [x.id for x in rec.line_partial_ids]
            if line_ids:
                cr.execute(
                    "SELECT account_id, reconcile_partial_id "
                    "FROM account_move_line "
                    "WHERE id IN %s "
                    "GROUP BY account_id, reconcile_partial_id",
                    (tuple(line_ids), ))
                res = cr.fetchall()
                if len(res) != 1:
                    raise Warning(_(
                        "Entries are not of the same account "
                        "or already reconciled ! "))
        return super(account_move_reconcile, self).reconcile_partial_check(
            cr, uid, ids, type=type, context=context)
