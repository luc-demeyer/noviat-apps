# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
# 
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from tools.translate import _
import logging

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def action_cancel(self, cr, uid, ids, *args):
        voucher_obj = self.pool.get('account.voucher')
        for invoice in self.browse(cr, uid, ids):
                voucher_ids = voucher_obj.search(cr, uid, [('invoice_id', '=', invoice.id)])
                voucher_obj.unlink(cr, uid, voucher_ids)
                if voucher_ids:
                    logging.getLogger(self._name).debug('action_cancel, voucher(s) %s have been unlinked', voucher_ids)
        return super(account_invoice, self).action_cancel(cr, uid, ids, *args)

account_invoice()
