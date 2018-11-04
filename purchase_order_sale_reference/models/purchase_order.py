# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_sale_order_count',
        search='_search_sale_order_ids',
        string='Sale Orders')
    sale_order_count = fields.Integer(
        compute='_compute_sale_order_count',
        string='# of Sales Order')

    @api.model
    def _search_sale_order_ids(self, operator, value):
        if operator == 'in':
            if isinstance(value, int):
                value = [value]
            po_ids = self.env['procurement.order'].search(
                [('sale_order_id', 'in', value),
                 ('state', '!=', 'cancel')
                 ]).mapped('purchase_id.id')
            return [('id', 'in', po_ids)]
        else:
            raise UserError(_('Unsupported operand for search!'))

    @api.one
    def _compute_sale_order_count(self):
        procs = self.env['procurement.order'].search(
            [('purchase_id', '=', self.id),
             ('state', '!=', 'cancel')
             ])
        self.sale_order_ids = procs.mapped('sale_order_id')
        self.sale_order_count = len(self.sale_order_ids)

    @api.multi
    def view_sale_order(self):
        self.ensure_one()
        action = {}
        so_ids = [x.id for x in self.sale_order_ids]
        if so_ids:
            form = self.env.ref('sale.view_order_form')
            if len(so_ids) > 1:
                tree = self.env.ref(
                    'sale.view_order_tree')
                action.update({
                    'name': _('Sales Orders'),
                    'view_mode': 'tree,form',
                    'views': [(tree.id, 'tree'), (form.id, 'form')],
                    'domain': [('id', 'in', so_ids)],
                })
            else:
                action.update({
                    'name': _('Sales Order'),
                    'view_mode': 'form',
                    'view_id': form.id,
                    'res_id': so_ids[0],
                })
            action.update({
                'context': self._context,
                'view_type': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
            })
        return action
