# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2011 Noviat nv/sa (www.noviat.be). All rights reserved.
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

from tools.translate import _
from osv import fields, osv
import netsvc
logger=netsvc.Logger()

class nov_print_journal_fiscalyear(osv.osv_memory):
    _name = 'nov.partner.ledger.fy.close' 
    _description = 'Print Open Receivables/Payables by Fiscal Year'

    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year', required=True),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
        'result_selection': fields.selection([('customer','Receivable Accounts'),
                                              ('supplier','Payable Accounts'),
                                              ('customer_supplier','Receivable and Payable Accounts')],
                                              "Partner's", required=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True)
    }    
    _defaults={
        'target_move': 'posted',
        'result_selection': 'customer',
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'account.coda', context=c),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]       
        data.update( {'ids': [data['fiscalyear_id']], 'model': 'account.fiscalyear'} )
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'nov.account.partner.ledger.fy.close.print',
            'datas': data,
        }

nov_print_journal_fiscalyear()
