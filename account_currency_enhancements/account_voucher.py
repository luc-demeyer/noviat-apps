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

from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)


class account_voucher(orm.Model):
    _inherit = 'account.voucher'

    def _check_paid(self, cr, uid, ids, name, args, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            #res[voucher.id] = any([((line.account_id.type, 'in', ('receivable', 'payable')) and line.reconcile_id) for line in voucher.move_ids])
            res[voucher.id] = any([((line.account_id.type in ('receivable', 'payable')) and line.reconcile_id) for line in voucher.move_ids])  # FIX by Noviat
        return res

    _columns = {
        'paid': fields.function(_check_paid, string='Paid', type='boolean', help="The Voucher has been totally paid."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
