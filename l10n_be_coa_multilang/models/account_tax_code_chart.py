# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountTaxCodeChart(models.Model):
    _name = 'account.tax.code.chart'
    _inherit = 'l10n.be.chart.common'
    _description = 'Tax Tag Code Chart'
    _parent_store = True
    _order = 'sequence, code'

    name = fields.Char(
        required=True, translate=True)
    code = fields.Char()
    info = fields.Text()
    parent_id = fields.Many2one(
        comodel_name='account.tax.code.chart',
        string='Parent Code', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name='account.tax.code.chart',
        inverse_name='parent_id',
        string='Child Codes')
    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        help="Country for which this Chart is used")

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for case in self:
            if case.code:
                name = ' - '.join([case.code, case.name])
            else:
                name = case.name
            result.append((case.id, name))
        return result
