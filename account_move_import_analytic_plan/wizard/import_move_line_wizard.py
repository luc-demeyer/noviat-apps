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

from openerp.osv import orm
from openerp.tools.translate import _


class AccountMoveLineImport(orm.TransientModel):
    _inherit = 'aml.import'

    def _input_fields(self):
        res = super(AccountMoveLineImport, self)._input_fields()
        res['analytic distribution'] = {'method': self._handle_analytic_plan}
        return res

    def _handle_analytic_plan(self, cr, uid,
                              field, line, move, aml_vals, context=None):
        if not aml_vals.get('analytics_id'):
            plan_inst_obj = self.pool['account.analytic.plan.instance']
            input = line[field]
            dom1 = [('code', '=', input)]
            dom2 = [('name', '=', input)]
            ctx = context and context.copy() or {}
            ctx['journal_id'] = move.journal_id.id
            for dom in [dom1, dom2]:
                plan_inst_ids = plan_inst_obj.search(
                    cr, uid, dom, context=ctx)
                if len(plan_inst_ids) == 1:
                    aml_vals['analytics_id'] = plan_inst_ids[0]
                    break
                elif len(plan_inst_ids) > 1:
                    msg = _("Multiple Analytic Distributions found "
                            "that match with '%s' !") % input
                    self._log_line_error(line, msg)
                    break
            if not plan_inst_ids:
                msg = _("Invalid Analytic Distribution '%s' !") % input
                self._log_line_error(line, msg)
