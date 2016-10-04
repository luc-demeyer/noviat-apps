# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
