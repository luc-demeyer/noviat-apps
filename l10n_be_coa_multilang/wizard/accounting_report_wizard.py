# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from openerp.osv import orm
#import logging
#_logger = logging.getLogger(__name__)


class accounting_report(orm.TransientModel):
    _inherit = 'accounting.report'

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = super(accounting_report, self)._build_contexts(cr, uid, ids, data, context=context)
        #_logger.warn('_build_contexts, ids = %s, data = %s, context = %s', ids, data, context)
        if context.get('lang'):
            result.update({'lang': context.get('lang')})
        account_report_id = self.read(cr, uid, ids, ['account_report_id'], context=context)[0]['account_report_id'][0]
        mod_obj = self.pool.get('ir.model.data')
        module = 'l10n_be_coa_multilang'
        xml_ids = ['account_financial_report_BE_2_FULL', 'account_financial_report_BE_3_FULL']
        be_legal_report_ids = []
        for xml_id in xml_ids:
            be_legal_report_ids.append(mod_obj.get_object_reference(cr, uid, module, xml_id)[1])
        if account_report_id in be_legal_report_ids:
            result.update({'get_children_by_sequence': True})
        # To DO : set 'code_print' flag based upon parameter that can be set by end-user
        result.update({'code_print': True})
        return result

