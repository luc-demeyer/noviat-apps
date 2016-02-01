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


from openerp import models, fields, api


class AccountCodaTransCategory(models.Model):
    _name = 'account.coda.trans.category'
    _description = 'CODA transaction category'
    _rec_name = "display_name"

    category = fields.Char(
        string='Transaction Category', size=3, required=True)
    description = fields.Char(string='Description', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('category', 'description')
    def _compute_display_name(self):
        display_name = self.category
        if self.description:
            display_name += ' ' + self.description
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(
                [('category', 'like', name)] + args, limit=limit)
        if not recs:
            recs = self.search(
                [('description', operator, name)] + args, limit=limit)
        return [(r.id, r.display_name) for r in recs]
