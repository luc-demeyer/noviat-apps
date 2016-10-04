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


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    @api.multi
    def compute_refund(self, mode='refund'):
        result = super(AccountInvoiceRefund, self).compute_refund(mode)
        refund_ids = [x[2] for x in result['domain']
                      if x[0] == 'id' and x[1] == 'in']
        if refund_ids:
            refund_id = refund_ids[0] and refund_ids[0][0] or False
        if refund_id:
            refund = self.env['account.invoice'].browse(refund_id)
            accrual_lines = {}
            accrual_accounts = []
            for aml in refund.accrual_move_id.line_id:
                product = aml.product_id
                if aml.account_id not in accrual_accounts:
                    accrual_account = product.accrued_expense_account_id
                    if not accrual_account:
                        accrual_account = product.product_tmpl_id.\
                            get_accrued_expense_account()
                    if accrual_account:
                        accrual_accounts.append(accrual_account)
                    else:
                        continue
                accrual_lines[product.id] = aml
            for origin_invoice in refund.origin_invoices_ids:
                for orig_aml in origin_invoice.accrual_move_id.line_id:
                    if orig_aml.account_id in accrual_accounts \
                            and not orig_aml.reconcile_id:
                        if orig_aml.product_id.id in accrual_lines:
                            accrual_lines[orig_aml.product_id.id] += orig_aml
            if accrual_lines:
                refund._reconcile_accrued_expense_lines(accrual_lines)
        return result
