# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        compute='_compute_sale_order_id',
        string='Sale Order',
        store=True, readonly=True)

    @api.one
    @api.depends('group_id')
    def _compute_sale_order_id(self):
        if self.group_id:
            self.sale_order_id = self.env['sale.order'].search(
                [('procurement_group_id', '=', self.group_id.id)])
