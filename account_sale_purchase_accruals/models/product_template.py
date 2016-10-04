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

from openerp import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    accrued_expense_in_account_id = fields.Many2one(
        'account.account', string='Accrued Expense In Account',
        domain=[('type', 'not in', ['view', 'closed', 'consolidation'])],
        company_dependent=True,
        help="Set this account to create an accrual for the cost of goods "
             "or services during the procurement operation.")
    accrued_expense_out_account_id = fields.Many2one(
        'account.account', string='Accrued Expense Out Account',
        domain=[('type', 'not in', ['view', 'closed', 'consolidation'])],
        company_dependent=True,
        help="Set this account to create an accrual for the cost of goods "
             "or services during the sales operation.")
    recursive_accrued_expense_in_account_id = fields.Many2one(
        'account.account', string='Accrued Expense In Account',
        compute='_compute_recursive_accrued_expense_in_account_id',
        help="Accrued Expense In Account on "
             "Product Record or Product Category.")
    recursive_accrued_expense_out_account_id = fields.Many2one(
        'account.account', string='Accrued Expense Out Account',
        compute='_compute_recursive_accrued_expense_out_account_id',
        help="Accrued Expense Out Account "
             "on Product Record or Product Category.")
    recursive_property_stock_account_input = fields.Many2one(
        'account.account', string='Stock Input Account',
        compute='_compute_recursive_property_stock_account_input',
        help="Stock Input Account on "
             "Product Record or Product Category.")
    recursive_property_stock_account_output = fields.Many2one(
        'account.account', string='Stock Output Account',
        compute='_compute_recursive_property_stock_account_output',
        help="Stock Output Account "
             "on Product Record or Product Category.")

    @api.one
    def _compute_recursive_accrued_expense_in_account_id(self):
        if self.accrued_expense_in_account_id:
            account = self.accrued_expense_in_account_id
        elif self.categ_id:
            account = self.categ_id.get_accrued_expense_in_account()
        else:
            account = self.env['account.account']
        self.recursive_accrued_expense_in_account_id = account

    @api.one
    def _compute_recursive_accrued_expense_out_account_id(self):
        if self.accrued_expense_out_account_id:
            account = self.accrued_expense_out_account_id
        elif self.categ_id:
            account = self.categ_id.get_accrued_expense_out_account()
        else:
            account = self.env['account.account']
        self.recursive_accrued_expense_out_account_id = account

    @api.one
    def _compute_recursive_property_stock_account_input(self):
        if self.property_stock_account_input:
            account = self.property_stock_account_input
        elif self.categ_id:
            account = self.categ_id.get_property_stock_account_input()
        else:
            account = self.env['account.account']
        self.recursive_property_stock_account_input = account

    @api.one
    def _compute_recursive_property_stock_account_output(self):
        if self.property_stock_account_output:
            account = self.property_stock_account_output
        elif self.categ_id:
            account = self.categ_id.get_property_stock_account_output()
        else:
            account = self.env['account.account']
        self.recursive_property_stock_account_output = account
