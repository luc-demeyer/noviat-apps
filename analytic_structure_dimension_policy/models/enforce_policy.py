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

from openerp import _
from openerp.exceptions import Warning as UserError


class EnforcePolicy(object):

    def _enforce_account_type_policy(self, analytic, policy=None):
        """
        Enforce Account Type Analytic Dimension Policy
        """
        if not policy:
            try:
                policy = self.account_id.user_type.\
                    analytic_dimension_policy
            except:
                raise UserError(_(
                    "Programming Error"
                    "\nUnable to get Account Type Policy for object '%s'")
                    % self._name)

        if policy in ('always', 'never'):
            for prefix, model in analytic.iteritems():
                for s in self.env['analytic.structure'].get_structures(model):
                    dim = s.nd_id
                    if dim.enforce_account_type_policy:
                        field = '%s%s_id' % (prefix, s.ordering)
                        val = getattr(self, field)
                        if policy == 'always' and not val:
                            raise UserError(_(
                                "Field '%s' is a required field !")
                                % dim.name)
                        elif policy == 'never' and val:
                            raise UserError(_(
                                "Field '%s' must be empty !")
                                % dim.name)
