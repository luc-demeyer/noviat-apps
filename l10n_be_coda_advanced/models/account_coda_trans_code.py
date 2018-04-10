# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountCodaTransCode(models.Model):
    _name = 'account.coda.trans.code'
    _description = 'CODA transaction code'
    _rec_name = 'description'

    code = fields.Char(string='Code', size=2, required=True)
    type = fields.Selection(
        [('code', 'Transaction Code'),
         ('family', 'Transaction Family')],
        string='Type', required=True)
    parent_id = fields.Many2one('account.coda.trans.code', string='Family')
    description = fields.Char(string='Description', translate=True)
    comment = fields.Text('Comment', translate=True)
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name", readonly=True)

    @api.one
    @api.depends('code', 'description', 'type', 'parent_id')
    def _compute_display_name(self):
        display_name = self.code
        if self.description:
            display_name += ' ' + self.description
        if self.type == 'code':
            family = self.parent_id.code
            display_name += ' (' + _('Family %s') % family + ')'
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
