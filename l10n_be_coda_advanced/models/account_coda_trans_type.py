# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
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


class AccountCodaTransType(models.Model):
    _name = 'account.coda.trans.type'
    _description = 'CODA transaction type'
    _rec_name = "display_name"

    type = fields.Char(string='Transaction Type', size=1, required=True)
    parent_id = fields.Many2one('account.coda.trans.type', string='Parent')
    description = fields.Text(string='Description', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('type', 'description')
    def _compute_display_name(self):
        display_name = self.type
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
            recs = self.search([('type', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search(
                [('description', operator, name)] + args, limit=limit)
        return [(r.id, r.display_name) for r in recs]
