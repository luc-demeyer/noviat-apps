# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.addons.account_sale_purchase_accruals.models.common_accrual \
    import CommonAccrual


class StockPicking(models.Model, CommonAccrual):
    _inherit = 'stock.picking'

    valuation_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='picking_id',
        string='Stock Valuation Journal Entries',
        readonly=True, copy=False)
    purchase_order_ids = fields.Many2many(
        comodel_name='purchase.order', compute='_compute_purchase_order_ids',
        string="Purchase Orders")

    @api.one
    def _compute_purchase_order_ids(self):
        stock_moves = self.move_lines
        po_lines = stock_moves.mapped('purchase_line_id')
        self.purchase_order_ids = po_lines.mapped('order_id')

    def _reconcile_invoice_accruals(self, pick_type):
        if pick_type == 'out':
            invoices = self.sale_id.invoice_ids
            inv_accruals = invoices.mapped('accrual_move_id')
            inv_amls = inv_accruals.mapped('line_id')
        else:
            invoices = self.purchase_order_ids.mapped('invoice_ids')
            inv_moves = invoices.mapped('move_id')
            inv_amls = inv_moves.mapped('line_id')
        if not invoices:
            return
        sp_amls = self.valuation_move_ids.mapped('line_id')

        accrual_lines = {}
        for sp_aml in sp_amls:
            product = sp_aml.product_id
            if pick_type == 'out':
                accrual_account = \
                    product.recursive_property_stock_account_output
            else:
                accrual_account = \
                    product.recursive_property_stock_account_input
            if accrual_account == sp_aml.account_id:
                if product.id not in accrual_lines:
                    accrual_lines[product.id] = self.env['account.move.line']
                accrual_lines[product.id] |= sp_aml
                for inv_aml in inv_amls:
                    if inv_aml.account_id == accrual_account \
                            and inv_aml.product_id == product:
                        accrual_lines[product.id] |= inv_aml

        if accrual_lines:
            self._reconcile_accrued_expense_lines(accrual_lines)

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        if self.picking_type_id.code == 'outgoing':
            self._reconcile_invoice_accruals('out')
        elif self.picking_type_id.code == 'incoming':
            self._reconcile_invoice_accruals('in')
        return res
