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

class nov_print_journal(osv.osv_memory):
    _name = 'nov.print.journal' 
    _description = 'l10n_be_coa_multilang - Print Journal by Period'

    _columns = {
        'journal_ids': fields.many2many('account.journal', 'npj_journal_rel', 'npj_id', 'journal_id', 'Journals', required=True),
        'period_ids': fields.many2many('account.period', 'npj_period_rel', 'npj_id', 'period_id', 'Periods', required=True),
        'sort': fields.selection([('date','Date'),('number','Number')],
            'Entries Sorted By', required=True),
        }
    
    _defaults={
        'sort': lambda *a: 'number'
            }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_move = self.pool.get('account.move')
        data = self.read(cr, uid, ids)[0]       
        journal_ids = data['journal_ids']
        period_ids = data['period_ids']
        sort = data['sort']       
        if type(period_ids)==type([]):      
            journal_ids_new = []
            for journal in journal_ids:
                for period in period_ids:
                    ids_move = obj_move.search(cr,uid, [('journal_id','=',journal),('period_id','=',period)], limit=1)
                    if ids_move:
                        journal_ids_new.append(journal)
            if not journal_ids_new:
                raise osv.except_osv(_('No Data Available'), _('No records found for your selection!'))           
        datas = {'ids': []}
        datas['model'] = 'account.journal'
        datas['journal_ids'] = journal_ids_new
        datas['period_ids'] = period_ids
        datas['sort'] = sort
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'nov.account.journal.period.print',
            'datas': datas,
        }

nov_print_journal()


