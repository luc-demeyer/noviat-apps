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

from openerp.osv import orm
from openerp.tools.translate import _
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)


class account_payment_populate_statement(orm.TransientModel):
    _inherit = "account.payment.populate.statement"

    def populate_statement(self, cr, uid, ids, context=None):
        res = super(
            account_payment_populate_statement, self
            ).populate_statement(cr, uid, ids, context=context)

        if context is None:
            context = {}
        st_obj = self.pool.get('account.bank.statement')
        st_id = context.get('active_id')
        if not st_id:
            return res
        st = st_obj.browse(cr, uid, st_id, context=context)
        st_name = st.name
        if st_name == '/':
            journal = st.journal_id
            if journal.sequence_id:
                c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
                st_name = self.pool['ir.sequence'].next_by_id(cr, uid, journal.sequence_id.id, context=c)
            else:
                raise orm.except_orm(
                    _('Error'),
                    _("Please define an Entry Sequence on your Bank Journal or fill in the Bank Statement Name !"))
            st.write({'name': st_name})

        wf_service = netsvc.LocalService('workflow')
        for st_line in st.line_ids:
            voucher = st_line.voucher_id
            if voucher.state == 'draft':
                number = st_name + '/' + str(st_line.sequence)
                voucher.write({'number': number})
                wf_service.trg_validate(
                    uid, 'account.voucher', st_line.voucher_id.id,
                    'proforma_voucher', cr)
        return res
