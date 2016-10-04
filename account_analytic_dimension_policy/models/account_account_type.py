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
#    Inspired by account_analytic_required module from
#    Alexis de Lattre <alexis.delattre@akretion.com>

from openerp import api, fields, models, _


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    analytic_dimension_policy = fields.Selection(
        '_get_policies', string='Policy for analytic dimension',
        required=True, default=lambda self: self._default_policy())

    @api.model
    def _get_policies(self):
        return [('optional', _('Optional')),
                ('always', _('Always')),
                ('never', _('Never'))]

    @api.model
    def _default_policy(self):
        return 'optional'

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type in ['none', 'asset', 'liabilty']:
            self.analytic_dimension_policy = 'never'
        else:
            self.analytic_dimension_policy = 'optional'
