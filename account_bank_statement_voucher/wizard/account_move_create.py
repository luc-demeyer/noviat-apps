# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from openerp.osv import orm
from openerp.tools.translate import _
#import logging
#_logger = logging.getLogger(__name__)
    
class account_move_create(orm.TransientModel):
    _name = 'account.move.create'
    _description = 'account.move.create'
    
    def create_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        statement_obj = self.pool.get('account.bank.statement')
        stline_obj = self.pool.get('account.bank.statement.line')
        st_line = stline_obj.browse(cr, uid, context['active_id'], context=context)
        statement = st_line.statement_id
        journal = statement.journal_id
        st_name = statement.name
        st_number = st_name
        st_line_number = statement_obj.get_next_st_line_number(cr, uid, st_number, st_line, context)
        company_currency_id = journal.company_id.currency_id.id
        move_id = stline_obj.create_move(cr, uid, st_line.id, company_currency_id, st_line_number, context=context)
        move_view = mod_obj.get_object_reference(cr, uid, 'account_bank_statement_voucher', 'view_move_from_bank_form')
        act_move = {
            'name': _('Journal Entry'),
            'res_id': move_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': [move_view[1]],
            'target': 'new',
            'context': dict(context, active_ids=ids),
            'type': 'ir.actions.act_window',
        }
        return act_move

