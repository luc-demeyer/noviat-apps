# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _prepare_account_move_line(self, move, qty, cost, credit_account_id,
                                   debit_account_id):
        res = super(StockQuant, self)._prepare_account_move_line(
            move, qty, cost, credit_account_id, debit_account_id)
        debit_line_vals = res[0][2]
        credit_line_vals = res[1][2]
        debit = debit_line_vals['debit']
        credit = credit_line_vals['credit']
        if not (debit or credit):
            cost, cost_cur, cur = \
                move.product_id._get_purchase_pricelist_amount(
                    qty, company=move.company_id)
            if cost > 0:
                debit_line_vals['debit'] = cost
                credit_line_vals['credit'] = cost
            else:
                debit_line_vals['credit'] = -cost
                credit_line_vals['debit'] = -cost
            if cur != move.company_id.currency_id:
                debit_line_vals['currency_id'] = cur.id
                debit_line_vals['amount_currency'] = cost_cur
                credit_line_vals['currency_id'] = cur.id
                credit_line_vals['amount_currency'] = -cost_cur
        return res

    @api.model
    def _create_account_move_line(self, quants, move, credit_account_id,
                                  debit_account_id, journal_id):
        ctx = dict(self._context,
                   picking_id=move.picking_id.id,
                   create_from_picking=True,
                   inventory_id=move.inventory_id.id,
                   create_from_inventory=True)
        super(StockQuant, self.with_context(ctx))._create_account_move_line(
            quants, move, credit_account_id, debit_account_id, journal_id)
