# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BeLegalFinancialReportChart(models.Model):
    _name = 'be.legal.financial.report.chart'
    _inherit = 'l10n.be.chart.common'
    _description = 'Belgian Legal Financial Report Chart'
    _parent_store = True
    _order = 'sequence, code'

    name = fields.Char(
        string='Report Name', required=True, translate=True)
    code = fields.Char(size=16)
    balance_factor = fields.Float(
        help="Specify here the factor that will be applied on the "
             "balance field of the Journal Items selected for this entry.")
    parent_id = fields.Many2one(
        comodel_name='be.legal.financial.report.chart',
        index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name='be.legal.financial.report.chart',
        inverse_name='parent_id',
        string='Child Entries')

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for entry in self:
            if entry.code:
                name = ' - '.join([entry.code, entry.name])
            else:
                name = entry.name
            result.append((entry.id, name))
        return result
