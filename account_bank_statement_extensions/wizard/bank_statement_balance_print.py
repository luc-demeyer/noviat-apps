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

import time
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class bank_statement_balance_print(orm.TransientModel):
    _name = 'bank.statement.balance.print'
    _description = 'Bank Statement Balances Report'
    _columns = {
        'date_balance': fields.date('Date', required=True),
        'journal_ids': fields.many2many('account.journal', 'account_journal_rel', 'bsbp_id', 'journal_id', 'Financial Journal(s)',
            domain=[('type', '=', 'bank')],
            help = 'Select here the Financial Journal(s) you want to include in your Bank Statement Balances Report.'),
    }

    def _get_journals(self, cr, uid, context=None):
        return self.pool.get('account.journal').search(cr, uid ,[('type', '=', 'bank')])

    _defaults = {
        'date_balance': lambda *a: time.strftime('%Y-%m-%d'),
        'journal_ids': _get_journals,
    }

    def balance_print(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        try:
            data = self.read(cr, uid, ids, [], context=context)[0]
        except:
            raise orm.except_orm(_('Error!'), _('Wizard in incorrect state. Please hit the Cancel button!'))
            return {}
        #_logger.warn('balance_print, data = %s', data)
        journal_ids = data['journal_ids']
        if not journal_ids:
            raise orm.except_orm(_('Warning'), _('No Financial Journals selected!'))
        datas = {
            'ids': [],
            'model': 'account.bank.statement',
            'date_balance': data['date_balance'],
            'journal_ids': journal_ids,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bank.statement.balance.report',
            'datas': datas,
        }

