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

from openerp import models, fields, api, _


class AccountCodaTransCode(models.Model):
    _name = 'account.coda.trans.code'
    _description = 'CODA transaction code'
    _rec_name = "display_name"

    code = fields.Char(string='Code', size=2, required=True)
    type = fields.Selection(
        [('code', 'Transaction Code'),
         ('family', 'Transaction Family')],
        string='Type', required=True)
    parent_id = fields.Many2one('account.coda.trans.code', string='Family')
    description = fields.Char(string='Description', translate=True)
    comment = fields.Text('Comment', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('code', 'description', 'type', 'parent_id')
    def _compute_display_name(self):
        display_name = self.code
        if self.description:
            display_name += ' ' + self.description
        if self.type == 'code':
            family = self.parent_id.code
            display_name += ' (' + _('Family %s') % family + ')'
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name
