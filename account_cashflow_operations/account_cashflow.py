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

from osv import fields, osv
from tools.translate import _

class account_cashflow_provision_line(osv.osv):
    _inherit = 'account.cashflow.provision.line'

    def _get_reference_model(self, cr, uid, context=None):
        res = super(account_cashflow_provision_line, self)._get_reference_model(cr, uid, context=context)
        res += [('account.cash.operation','Cash Management Operation')]
        return res
    
    _columns = {
        'origin': fields.reference('Originating Transaction', size=128, readonly=True,
            selection=_get_reference_model,
            help='This field contains a reference to the transaction that originated the creation of this provision.'),
    }

account_cashflow_provision_line()



        