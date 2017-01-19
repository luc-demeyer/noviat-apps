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
            vals['picking_id'] = context['picking_id']
        return super(AccountMove, self).create(vals, **kwargs)
