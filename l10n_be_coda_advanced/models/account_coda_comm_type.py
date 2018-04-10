# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountCodaCommType(models.Model):
    _name = 'account.coda.comm.type'
    _description = 'CODA structured communication type'
    _rec_name = 'description'

    code = fields.Char(
        string='Structured Communication Type', size=3, required=True)
    description = fields.Char(string='Description', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('code', 'description')
    def _compute_display_name(self):
        display_name = self.code
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
            recs = self.search([('code', 'like', name)] + args, limit=limit)
        if not recs:
            recs = self.search(
                [('description', operator, name)] + args, limit=limit)
        return [(r.id, r.display_name) for r in recs]

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
         "The Structured Communication Code must be unique !")
    ]
