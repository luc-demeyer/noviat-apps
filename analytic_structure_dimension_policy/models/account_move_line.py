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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.analytic_structure.MetaAnalytic import MetaAnalytic
from openerp.addons.analytic_structure_dimension_policy.models.enforce_policy\
    import EnforcePolicy
from openerp import api, models


class AccountMoveLine(models.Model, EnforcePolicy):
    """
    Inherit from EnforcePolicy for Account Type Policy Enforcement
    """
    __metaclass__ = MetaAnalytic
    _inherit = 'account.move.line'
    _analytic = 'account_move_line'

    @api.multi
    def _validate_analytic_fields(self, analytic):
        """
        Enforce Account Type Analytic Dimension Policy
        """
        for aml in self:
            aml._enforce_account_type_policy(
                analytic, policy=aml.analytic_dimension_policy)
        super(AccountMoveLine, self)._validate_analytic_fields(analytic)
