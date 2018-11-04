# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def import_lines(self):
        self.ensure_one()
        view = self.env.ref(
            '{}.stock_level_import_view_form'.format(self._module))
        return {
            'name': _('Import File'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.level.import',
            'view_id': view.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
