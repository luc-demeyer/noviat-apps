# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    valuation_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='inventory_id',
        string='Stock Valuation Journal Entries',
        readonly=True, copy=False)
