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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class account_move(orm.Model):
    _inherit = 'account.move'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        #_logger.warn('%s, search, args=%s, context=%s', self._name, args, context)
        if context is None: 
            context = {}
        if context.get('act_window_from_bank_statement_line'):
            absl_id = context.get('active_id')
            st_line = self.pool.get('account.bank.statement.line').browse(cr, uid, absl_id)
            moves = st_line.move_ids
            if moves:
                move_ids = [x.id for x in moves]
            else:
                move_ids = []
            args.append(('id', 'in', move_ids))
        #_logger.warn('%s, search, exit args=%s', self._name, args)
        return super(account_move, self).search(cr, uid, args, offset, limit, order, context, count)
