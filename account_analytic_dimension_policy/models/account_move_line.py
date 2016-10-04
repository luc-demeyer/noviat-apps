# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from openerp import fields, models


class AccountMoveLine(models.Model):
    """
    This module adds fields to facilitate UI enforcement
    of analytic dimensions.
    """
    _inherit = 'account.move.line'

    analytic_dimension_policy = fields.Selection(
        string='Policy for analytic dimension',
        related='account_id.analytic_dimension_policy', readonly=True)
    move_state = fields.Selection(
        string='Move State',
        related='move_id.state',
        readonly=True)

    def fields_get(self, cr, uid, allfields=None, context=None,
                   write_access=True, attributes=None):
        """
        force 'move_state' into non-required field to allow creation of
        account.move.line objects via the standard 'Journal Items' menu entry
        """
        res = super(AccountMoveLine, self).fields_get(
            cr, uid, allfields=allfields, context=context,
            write_access=write_access, attributes=attributes)
        if res.get('move_state'):
            res['move_state']['required'] = False
        return res
