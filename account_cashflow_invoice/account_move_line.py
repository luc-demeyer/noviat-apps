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

from osv import osv, fields
import re
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def reconcile(self, cr, uid, ids, *args, **kwargs):
        res = super(account_move_line,self).reconcile(cr, uid, ids, *args, **kwargs)
        cfpline_obj = self.pool.get('account.cashflow.provision.line')
        for move_line in self.browse(cr, uid, ids):
            inv = move_line.invoice
            if inv:
                domain = [ ('origin', '=', inv._name + ',' + str(inv.id))]
                cfpline_ids = cfpline_obj.search(cr, uid, domain)
                if len(cfpline_ids) > 1:
                    raise osv.except_osv(_('Warning'), _('Cash Flow Provision Line ambiguity, cf. lines %s') % cfpline_ids)
                elif len(cfpline_ids) == 1:
                    cfpline_obj.write(cr, uid, [cfpline_ids[0]], {'state': 'draft'})            
                    cfpline_obj.unlink(cr, uid, [cfpline_ids[0]])  
        return res

account_move_line()
