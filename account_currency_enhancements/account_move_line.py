# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.be). All rights reserved.
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
from openerp.tools.translate import _
from openerp import netsvc
import time
import logging
_logger = logging.getLogger(__name__)


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    def _check_currency(self, cr, uid, ids, context=None):
        res = super(account_move_line, self)._check_currency(cr, uid, ids, context=context)
        #for l in self.browse(cr, uid, ids, context=context):
        #    _logger.warn('l.account_id.code = %s, l.account_id.currency_id = %s, l.currency_id = %s, l.debit = %s, l.credit = %s', l.account_id.code, l.account_id.currency_id, l.currency_id, l.debit, l.credit)
        return res

    _constraints = [
        (_check_currency, "\n\nThe selected account of your Journal Entry enforces a pre-defined currency." \
            "\n\nYou should correct the currency of your transaction or otherwise ask your system administrator " \
            "to adjust the 'secondary currency' settings of the account.", 
            ['currency_id']),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
