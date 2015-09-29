# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from openerp.osv import orm, fields


class coda_account_mapping_rule(orm.Model):
    _inherit = 'coda.account.mapping.rule'

    _columns = {
        'analytics_id': fields.many2one(
            'account.analytic.plan.instance', 'Analytic Distribution'),
    }

    def _rule_select_extra(self, cr, uid,
                              coda_bank_account_id, context=None):
        return 'analytics_id, '

    def _rule_result_extra(self, cr, uid,
                              coda_bank_account_id, context=None):
        return ['analytics_id']
