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

from openerp import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_number = fields.Char(
        related='invoice_id.number', string='Invoice Number', readonly=True)
    invoice_type = fields.Selection(
        related='invoice_id.type', string='Invoice Type', readonly=True)
    invoice_state = fields.Selection(
        related='invoice_id.state', string='Invoice State', readonly=True)
    invoice_date = fields.Date(
        related='invoice_id.date_invoice', string='Invoice Date',
        readonly=True)
    invoice_journal_id = fields.Many2one(
        related='invoice_id.journal_id', string='Journal', readonly=True)
    invoice_partner_id = fields.Many2one(
        related='invoice_id.partner_id', string='Partner', readonly=True)

    @api.model
    def _report_xls_fields(self):
        """
        Adapt list in custom module to add/drop columns or change order.
        """
        return [
            'invoice_number', 'invoice_type', 'invoice_state',
            'journal', 'partner', 'date', 'account', 'description',
            'product', 'quantity', 'price_unit', 'discount',
            'price_subtotal', 'analytic_account',
            # 'partner_ref', 'product_ref', 'product_uos', 'note',
        ]

    @api.model
    def _report_xls_template(self):
        """
        Template updates, e.g.

        my_change = {
            'number':{
                'header': [1, 15, 'text', _('My Number Title')],
                'lines': [1, 0, 'text', _render("line.number or ''")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}
