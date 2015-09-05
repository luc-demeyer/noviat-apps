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

from openerp import models, fields


class account_journal(models.Model):
    _inherit = 'account.journal'

    payment_method_out = fields.Boolean(
        string="Outgoing Payment Method",
        help="If checked, this Journal becomes a Payment Method "
             "for the 'Register Payment' button on "
             "Supplier Invoices and Customer Credit Notes.")
    payment_date_out = fields.Selection(
        [('invoice_date', 'Invoice Date'),
         ('current_date', 'Now')],
        string="Outgoing Payment Date",
        help="Default date for the Payment.",
        default='invoice_date')
    payment_method_in = fields.Boolean(
        string="Incoming Payment Method",
        help="If checked, this Journal becomes a Payment Method "
             "for the 'Register Payment' button on "
             "Customer Invoices and Supplier Credit Notes.")
    payment_date_in = fields.Selection(
        [('invoice_date', 'Invoice Date'),
         ('current_date', 'Now')],
        string="Incoming Payment Date",
        help="Default date for the Payment.",
        default='current_date')
