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

from openerp import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    reinvoice_key_id = fields.Many2one(
        comodel_name='account.reinvoice.key',
        string='Reinvoice Key', index=True)
    reinvoice_line_ids = fields.One2many(
        comodel_name='account.reinvoice.line',
        inverse_name='move_line_in_id', readonly=True,
        string='Reinvoice Line')
    reinvoice_line_count = fields.Integer(
        compute='_compute_reinvoice_line_count',
        string='# of reinvoice lines')

    @api.one
    def _compute_reinvoice_line_count(self):
        self.reinvoice_line_count = len(self.reinvoice_line_ids)

    @api.multi
    def view_reinvoice_lines(self):
        self.ensure_one()
        action = {}
        arl_ids = [x.id for x in self.reinvoice_line_ids]
        if arl_ids:
            module = __name__.split('addons.')[1].split('.')[0]
            form = self.env.ref(
                '%s.account_reinvoice_line_form') % module
            if len(arl_ids) > 1:
                tree = self.env.ref(
                    '%s.account_reinvoice_line_tree') % module
                action.update({
                    'name': _('Reinvoice Lines'),
                    'view_mode': 'tree,form',
                    'views': [(tree.id, 'tree'), (form.id, 'form')],
                    'domain': [('id', 'in', arl_ids)],
                    })
            else:
                action.update({
                    'name': _('Reinvoice Line'),
                    'view_mode': 'form',
                    'view_id': form.id,
                    'res_id': arl_ids[0],
                    })
            action.update({
                'context': self._context,
                'view_type': 'form',
                'res_model': 'account.reinvoice.line',
                'type': 'ir.actions.act_window',
                })
        return action
