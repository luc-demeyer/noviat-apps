# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    accrued_expense_in_account_id = fields.Many2one(
        'account.account', string='Accrued Expense In Account',
        domain=[('type', 'not in', ['view', 'closed', 'consolidation'])],
        company_dependent=True, ondelete='restrict',
        help="Set this account to create an accrual for the cost of goods "
             "or services during the procurement operation.")
    accrued_expense_out_account_id = fields.Many2one(
        'account.account', string='Accrued Expense Out Account',
        domain=[('type', 'not in', ['view', 'closed', 'consolidation'])],
        company_dependent=True, ondelete='restrict',
        help="Set this account to create an accrual for the cost of goods "
             "or services during the sales operation.")

    @api.one
    @api.constrains('accrued_expense_in_account_id')
    def _check_accrued_expense_in_account_id(self):
        if self.accrued_expense_in_account_id:
            if not self.accrued_expense_in_account_id.reconcile:
                raise UserError(_(
                    "Please enable 'Allow Reconciliation' on "
                    "accrual account '%s'.")
                    % self.accrued_expense_in_account_id.code)

    @api.one
    @api.constrains('accrued_expense_out_account_id')
    def _check_accrued_expense_out_account_id(self):
        if self.accrued_expense_out_account_id:
            if not self.accrued_expense_out_account_id.reconcile:
                raise UserError(_(
                    "Please enable 'Allow Reconciliation' on "
                    "accrual account '%s'.")
                    % self.accrued_expense_out_account_id.code)

    @api.multi
    def get_accrued_expense_in_account(self):
        self.ensure_one()
        if self.accrued_expense_in_account_id:
            res = self.accrued_expense_in_account_id
        elif self.parent_id:
            res = self.parent_id.get_accrued_expense_in_account()
        else:
            res = self.env['account.account']
        return res

    @api.multi
    def get_accrued_expense_out_account(self):
        self.ensure_one()
        if self.accrued_expense_out_account_id:
            res = self.accrued_expense_out_account_id
        elif self.parent_id:
            res = self.parent_id.get_accrued_expense_out_account()
        else:
            res = self.env['account.account']
        return res

    @api.multi
    def get_property_stock_account_input(self):
        self.ensure_one()
        if self.property_stock_account_input_categ:
            res = self.property_stock_account_input_categ
        elif self.parent_id:
            res = self.parent_id.get_property_stock_account_input()
        else:
            res = self.env['account.account']
        return res

    @api.multi
    def get_property_stock_account_output(self):
        self.ensure_one()
        if self.property_stock_account_output_categ:
            res = self.property_stock_account_output_categ
        elif self.parent_id:
            res = self.parent_id.get_property_stock_account_input()
        else:
            res = self.env['account.account']
        return res
