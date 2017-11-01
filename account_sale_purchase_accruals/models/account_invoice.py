# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models, _
from openerp.addons.account_sale_purchase_accruals.models.common_accrual \
    import CommonAccrual
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model, CommonAccrual):
    _inherit = 'account.invoice'

    accrual_move_id = fields.Many2one(
        'account.move', string='Accrual Journal Entry',
        readonly=True, index=True, ondelete='set null', copy=False,
        help="Link to the automatically generated Accrual Entry.")
    purchase_order_ids = fields.Many2many(
        comodel_name='purchase.order', compute='_compute_purchase_order_ids',
        string="Purchase Orders")
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order', compute='_compute_sale_order_ids',
        string="Sale Orders")

    def _prepare_accrual_move_ref(self):
        sale_orders = self.sale_order_ids
        return ', '.join([x.name for x in sale_orders])

    @api.one
    def _compute_purchase_order_ids(self):
        dom = [('invoice_ids', '=', self.id)]
        self.purchase_order_ids = self.env['purchase.order'].search(dom)

    @api.one
    def _compute_sale_order_ids(self):
        dom = [('invoice_ids', '=', self.id)]
        self.sale_order_ids = self.env['sale.order'].search(dom)

    def _customer_invoice_create_expense_accruals(self):
        """
        - Create Accrual entries for the Customer Invoice.
        - Reconcile these entries with it's counterpart created during the
          Procurement Process in case of dropshipping
          (Purchase Order Confirmation) or
          the Outgoing Shipment in case of delivery from stock(.
        """
        aml_vals = []
        inv_accruals = {}
        inv_accrual_accounts = []
        partner = self.partner_id.commercial_partner_id

        # find associated pickings or purchase orders
        so_dom = [('sale_order_id', 'in', self.sale_order_ids._ids)]
        procs = self.env['procurement.order'].search(so_dom)
        proc_groups = procs.mapped('group_id')
        sp_dom = [('group_id', 'in', proc_groups._ids)]
        stock_pickings = self.env['stock.picking'].search(sp_dom)
        purchase_orders = procs.mapped('purchase_id')
        # pass the invoice date in the context
        # in order to retrieve the correct purchase price
        # for the expense accruals
        ctx_date = dict(self._context,
                        date=self.date_invoice,
                        date_p=self.date_invoice)

        for ail in self.with_context(ctx_date).invoice_line:
            product = ail.product_id

            if not product:
                continue

            procurement_action = ail._get_procurement_action()
            if procurement_action == 'move':
                if product.valuation == 'real_time':
                    accrual_account = \
                        product.recursive_property_stock_account_output
                else:
                    continue
            elif procurement_action == 'buy':
                accrual_account = \
                    product.recursive_accrued_expense_out_account_id
            else:
                continue

            if accrual_account:

                inv_accrual_accounts.append(accrual_account)
                expense_account = product.property_account_expense
                if not expense_account:
                    expense_account = product.categ_id.\
                        property_account_expense_categ
                if not expense_account:
                    raise UserError(
                        _("No 'Expense Account' defined for "
                          "product '%s' or the product category")
                        % product.name)
                fpos = partner.property_account_position
                if fpos:
                    expense_account = fpos.map_account(expense_account)
                amount, amount_cur, cur = product._get_expense_accrual_amount(
                    ail.quantity, procurement_action,
                    company=self.company_id)
                if self.type == 'out_refund':
                    amount = -amount
                    amount_cur = -amount_cur
                if not amount:
                    _logger.error(
                        _("No 'Cost' defined for product '%s'")
                        % product.name)

                expense_vals = {
                    'account_id': expense_account.id,
                    'debit': amount > 0 and amount or 0.0,
                    'credit': amount < 0 and -amount or 0.0,
                    'product_id': product.id,
                    'quantity': ail.quantity,
                    'partner_id': partner.id,
                    'name': ail.name,
                    'analytic_account_id': ail.account_analytic_id.id,
                    'entry_type': 'expense',
                }
                aml_vals.append(expense_vals)

                accrual_vals = {
                    'account_id': accrual_account.id,
                    'debit': expense_vals['credit'],
                    'credit': expense_vals['debit'],
                    'product_id': product.id,
                    'quantity': ail.quantity,
                    'partner_id':
                        procurement_action == 'move' and partner.id or False,
                    'name': ail.name,
                    'entry_type': 'accrual',
                }
                if cur:
                    accrual_vals.update({
                        'amount_currency': -amount_cur,
                        'currency_id': cur.id,
                    })
                aml_vals.append(accrual_vals)

        if aml_vals:
            am_id, inv_accruals = self._create_accrual_move(aml_vals)
            self.write({'accrual_move_id': am_id})

        # reconcile with Stock Valuation or PO accruals
        accruals = self.env['account.move']
        if stock_pickings:
            accruals |= stock_pickings.mapped('valuation_move_ids')
        if purchase_orders:
            accruals |= purchase_orders.mapped('s_accrual_move_id')
        if accruals:
            amls = accruals.mapped('line_id')
            for aml in amls:
                if aml.product_id.id in inv_accruals \
                        and aml.account_id in inv_accrual_accounts:
                    inv_accruals[aml.product_id.id] += aml
            self.with_context(ctx_date)._reconcile_accrued_expense_lines(
                inv_accruals, writeoff_period_id=self.period_id.id)

        # reconcile refund accrual with original invoice accrual
        # remark: this operation may fail, e.g. if original invoice
        # accrual is already reconciled during procurement proces.
        accrual_lines = {}
        for aml in self.accrual_move_id.line_id:
            if aml.account_id in inv_accrual_accounts:
                accrual_lines[aml.product_id.id] = aml
        # Logic infra doesn't cover refund validated via refund wizard
        # since origin_invoices_ids field is populated after the validation.
        # As a consequence we have added the same logic to the refund wizard.
        for origin_invoice in self.origin_invoices_ids:
            for orig_aml in origin_invoice.accrual_move_id.line_id:
                if orig_aml.account_id in inv_accrual_accounts \
                        and not orig_aml.reconcile_id:
                    if orig_aml.product_id.id in accrual_lines:
                        accrual_lines[orig_aml.product_id.id] += orig_aml
        if accrual_lines:
            self.with_context(ctx_date)._reconcile_accrued_expense_lines(
                accrual_lines, writeoff_period_id=self.period_id.id)

    def _supplier_invoice_reconcile_accruals(self):
        """
        Reconcile the accrual entries of the
        Purchase Invoice with it's counterpart created during the
        Purchase Order Confirmation or Incoming Picking.
        """
        si_amls = self.move_id.line_id
        accrual_lines = {}
        for si_aml in si_amls:
            product = si_aml.product_id
            if product:
                accrual_account = \
                    product.recursive_property_stock_account_input
                if si_aml.account_id == accrual_account:
                    accrual_lines[product.id] = si_aml
                    pickings = self.purchase_order_ids.mapped('picking_ids')
                    accruals = pickings.mapped('valuation_move_ids')
                else:
                    accrual_account = \
                        product.recursive_accrued_expense_in_account_id
                    if accrual_account \
                            and si_aml.account_id == accrual_account:
                        accrual_lines[product.id] = si_aml
                        accruals = self.purchase_order_ids.mapped(
                            'p_accrual_move_id')
                    else:
                        return
                amls = accruals.mapped('line_id')
                for aml in amls:
                    if aml.account_id == accrual_account \
                            and aml.product_id == product:
                        accrual_lines[product.id] += aml
        if accrual_lines:
            ctx = dict(self._context, date_p=self.date_invoice)
            self.with_context(ctx)._reconcile_accrued_expense_lines(
                accrual_lines, writeoff_period_id=self.period_id.id)

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for inv in self:
            if inv.type in ('out_invoice', 'out_refund'):
                inv._customer_invoice_create_expense_accruals()
            elif inv.type == 'in_invoice':
                inv._supplier_invoice_reconcile_accruals()
        return res

    @api.multi
    def action_cancel(self):
        for inv in self:
            if inv.accrual_move_id:
                inv.accrual_move_id.button_cancel()
                inv.accrual_move_id.unlink()
        return super(AccountInvoice, self).action_cancel()
