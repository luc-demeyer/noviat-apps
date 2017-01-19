# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _create_account_move_line(self, quants, move, credit_account_id,
                                  debit_account_id, journal_id):
        ctx = dict(self._context,
                   picking_id=move.picking_id.id,
                   create_from_picking=True)
        super(StockQuant, self.with_context(ctx))._create_account_move_line(
            quants, move, credit_account_id, debit_account_id, journal_id)
