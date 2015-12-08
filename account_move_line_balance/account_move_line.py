# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013-2015 Noviat nv/sa (www.noviat.com).
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
from lxml import etree
# import logging
# _logger = logging.getLogger(__name__)


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def _absolute_balance(self, cr, uid, ids, name, arg, context=None):
        cr.execute(
            "SELECT id, abs(debit-credit) "
            "FROM account_move_line WHERE id IN %s",
            (tuple(ids),))
        return dict(cr.fetchall())

    _columns = {
        'absolute_balance': fields.function(
            _absolute_balance,
            string='Absolute Amount', store=True,
            help="Absolute Amount in Company Currency"),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(account_move_line, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            aml_tree = etree.XML(res['arch'])
            pos = 0
            credit_pos = False
            done = False
            for el in aml_tree:
                pos += 1
                if el.tag == 'field':
                    if el.get('name') == 'credit':
                        credit_pos = pos
            if not done and credit_pos:
                absolute_balance_node = etree.Element(
                    'field', name='absolute_balance')
                aml_tree.insert(credit_pos, absolute_balance_node)
                absolute_balance_dict = self.fields_get(
                    cr, uid, ['absolute_balance'], context=context
                    )['absolute_balance']
                orm.setup_modifiers(
                    absolute_balance_node, absolute_balance_dict,
                    context=context, in_tree_view=True)
                res['fields']['absolute_balance'] = absolute_balance_dict
                done = True
            if done:
                res['arch'] = etree.tostring(aml_tree, pretty_print=True)
            # _logger.warn('arch=%s', res['arch'])
            # _logger.warn('fields=%s', res['fields'])
        return res
