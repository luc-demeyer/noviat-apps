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

from openerp import api, models


class AnalyticStructure(models.Model):
    _inherit = 'analytic.structure'

    @api.model
    def get_dimensions_and_policy(self, model):
        """
        Return a dictionary that contains
        - keys: the identifier
        - values: a dictionary with
             ordering
             dimension names
             enforce_account_type_policy flag
        of the analytic dimensions linked to the given model.
        """
        res = {}
        for s in self.env['analytic.structure'].get_structures(model):
            dim = s.nd_id
            res[dim.id] = {
                'ordering': int(s.ordering),
                'name': dim.name,
                'account_type_policy': dim.enforce_account_type_policy,
                }
        return res
