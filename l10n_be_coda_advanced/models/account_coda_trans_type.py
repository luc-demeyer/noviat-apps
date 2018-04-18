# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountCodaTransType(models.Model):
    _name = 'account.coda.trans.type'
    _description = 'CODA transaction type'
    _order = 'type'

    name = fields.Char(compute='_compute_name', readonly=True)
    type = fields.Char(string='Transaction Type', size=1, required=True)
    parent_id = fields.Many2one('account.coda.trans.type', string='Parent')
    description = fields.Text(string='Description', translate=True)

    @api.one
    @api.depends('type', 'description')
    def _compute_name(self):
        name = self.type
        if self.description:
            name += ' ' + self.description
        self.name = len(name) > 55 \
            and name[:55] + '...' \
            or name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('type', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search(
                [('description', operator, name)] + args, limit=limit)
        return [(r.id, r.name) for r in recs]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not args:
            args = []
        new_args = []
        for arg in args:
            if len(arg) == 3 and arg[0] == 'name':
                new_arg = ['|',
                           ('type', arg[1], arg[2]),
                           ('description', arg[1], arg[2])]
                new_args += new_arg
            else:
                new_args.append(arg)
        return super(AccountCodaTransType, self).search(
            new_args, offset=offset, limit=limit, order=order, count=count)
