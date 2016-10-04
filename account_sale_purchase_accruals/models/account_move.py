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

from openerp import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one(
        comodel_name='stock.picking', index=True,
        string='Stock Picking', ondelete='cascade')

    @api.model
    def create(self, vals, **kwargs):
        context = self._context
        if context.get('create_from_picking'):
            vals['picking_id'] = context['picking_id']
        return super(AccountMove, self).create(vals, **kwargs)
