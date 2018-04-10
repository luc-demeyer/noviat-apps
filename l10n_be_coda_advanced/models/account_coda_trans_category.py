# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountCodaTransCategory(models.Model):
    _name = 'account.coda.trans.category'
    _description = 'CODA transaction category'
    _rec_name = 'description'

    category = fields.Char(
        string='Transaction Category', size=3, required=True)
    description = fields.Char(string='Description', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('category', 'description')
    def _compute_display_name(self):
        display_name = self.category
        if self.description:
            display_name += ' ' + self.description
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(
                [('category', 'like', name)] + args, limit=limit)
        if not recs:
            recs = self.search(
                [('description', operator, name)] + args, limit=limit)
        return [(r.id, r.display_name) for r in recs]
