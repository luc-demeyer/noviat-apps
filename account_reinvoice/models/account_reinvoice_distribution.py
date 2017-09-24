# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountReinvoiceDistribution(models.Model):
    _name = 'account.reinvoice.distribution'
    _description = 'Reinvoice Distribution'
    _order = 'name'

    name = fields.Char(
        string='Name', index=True, required=True)
    description = fields.Char(
        string='Description')
    distribution_line_ids = fields.One2many(
        comodel_name='account.reinvoice.distribution.line',
        inverse_name='distribution_id', copy=True,
        string='Reinvoice Distribution Lines')
    active = fields.Boolean(
        string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company')
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name",
        store=True, readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'The Reinvoice Distribution must be unique per Company!'),
    ]

    def init(self, cr):
        cr.execute("""
            DROP INDEX IF EXISTS reinvoice_distribution_cpy_null_names_unique;
            CREATE UNIQUE INDEX reinvoice_distribution_cpy_null_names_unique
            ON account_reinvoice_distribution (name)
            WHERE company_id IS NULL;
        """)

    @api.one
    @api.depends('name', 'description')
    def _compute_display_name(self):
        display_name = self.name
        if self.description:
            display_name += ' ' + self.description
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        default['name'] = self.name + " (copy)"
        return super(AccountReinvoiceDistribution, self).copy(default)


class AccountReinvoiceDistributionLine(models.Model):
    _name = 'account.reinvoice.distribution.line'
    _description = 'Reinvoice Distribution Line'
    _order = 'sequence'

    distribution_id = fields.Many2one(
        comodel_name='account.reinvoice.distribution',
        string='Reinvoice Distribution',
        ondelete='cascade', index=True)
    sequence = fields.Integer(
        string='Sequence', default=10)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        required=True, index=True)
    rate = fields.Float(
        string='Rate (%)', required=True, digits=(16, 2))
