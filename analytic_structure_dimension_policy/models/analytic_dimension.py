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


class AnalyticDimension(models.Model):
    _inherit = 'analytic.dimension'

    enforce_account_type_policy = fields.Boolean(
        string='Enforce Account Type Policy',
        help="Enforce Analytic Dimension Policy "
             "defined on the Account Type."
             "\nThis enforcement will take place when "
             "encoding dimensions on the following objects:"
             "\n- Journal Items (account.move.line)"
             "\n- Invoice Lines (account.invoice.line)")
