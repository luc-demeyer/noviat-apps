# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _get_procurement_action(self):
        action = False
        product = self.product_id
        if product.type in ('product', 'consu'):
            dom = [
                ('invoice_lines', '=', self.id),
                ('product_id', '=', product.id)]
            sols = self.env['sale.order.line'].search(dom)
            procs = sols.mapped('procurement_ids')
            rules = procs.mapped('rule_id')
            actions = rules.mapped('action')
            if len(actions) == 1:
                action = actions[0]
        return action
