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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class res_company(models.Model):
    _inherit = 'res.company'

    in_inv_cd_account_id = fields.Many2one(
        'account.account',
        string='Incoming Invoice Cash Discount Account',
        required=True, domain=[('type', '=', 'other')],
        help="Default Cash Discount Account on incoming Invoices.")
    out_inv_cd_account_id = fields.Many2one(
        'account.account',
        string='Outgoing Invoice Cash Discount Account',
        required=True, domain=[('type', '=', 'other')],
        help="Default Cash Discount Account on outgoing Invoices.")
    out_inv_cd_term = fields.Integer(
        string='Outgoing Invoice Cash Discount Term',
        required=True,
        help="Default Cash Discount Term (in days) on outgoing Invoices.")
