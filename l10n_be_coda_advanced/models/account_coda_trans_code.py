# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountCodaTransCode(models.Model):
    _name = 'account.coda.trans.code'
    _description = 'CODA transaction code'
    _order = 'code'

    name = fields.Char(
        compute='_compute_name', readonly=True)
    code = fields.Char(string='Code', size=2, required=True)
    type = fields.Selection(
        [('code', 'Transaction Code'),
         ('family', 'Transaction Family')],
        string='Type', required=True)
    parent_id = fields.Many2one('account.coda.trans.code', string='Family')
    description = fields.Char(string='Description', translate=True)
    comment = fields.Text('Comment', translate=True)

    @api.one
    @api.depends('code', 'description', 'type', 'parent_id')
    def _compute_name(self):
        name = self.code
        if self.description:
            name += ' ' + self.description
        if self.type == 'code':
            family = self.parent_id.code
            name += ' (' + _('Family %s') % family + ')'
        self.name = len(name) > 55 \
            and name[:55] + '...' \
            or name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', 'like', name)] + args, limit=limit)
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
                           ('code', arg[1], arg[2]),
                           ('description', arg[1], arg[2])]
                new_args += new_arg
            else:
                new_args.append(arg)
        return super().search(
            new_args, offset=offset, limit=limit, order=order, count=count)
