# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
import logging
_logger = logging.getLogger(__name__)


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = { 
        'supplier_direct_debit': fields.boolean('Supplier Direct Debit',
            help="Set this flag to exclude Supplier Invoices from the Payment Order 'Select Invoices to Pay' selection."),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
            date_invoice, payment_term, partner_bank_id, company_id)
        if type == 'in_invoice' and partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            result['value']['supplier_direct_debit'] = partner.supplier_direct_debit
        return result

