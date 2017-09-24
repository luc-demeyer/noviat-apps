# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one(
        comodel_name='stock.picking', index=True,
        string='Stock Picking', ondelete='cascade')

    @api.model
    def create(self, vals, **kwargs):
        context = self._context
        if context.get('create_from_picking'):
            pick_id = context['picking_id']
            pick = self.env['stock.picking'].browse(pick_id)
            ref = vals.get('ref') or ''
            if pick.origin:
                ref += ' ' + pick.origin
            vals.update({
                'picking_id': pick_id,
                'ref': ref.strip()})
        if context.get('invoice'):
            ref = ''
            inv = context.get('invoice')
            if inv.reference:
                ref = inv.reference
            if inv.name and inv.name != inv.reference:
                ref += ' ' + inv.name
            if inv.origin and inv.origin not in [inv.reference, inv.name]:
                ref += ' ' + inv.origin
            vals['ref'] = ref.strip()
        return super(AccountMove, self).create(vals, **kwargs)
