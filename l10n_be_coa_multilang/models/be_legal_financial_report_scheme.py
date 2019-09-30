# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BeLegalFinancialReportscheme(models.Model):
    _name = 'be.legal.financial.report.scheme'
    _description = 'Belgian Legal Financial Report Scheme'
    _rec_name = 'account_group'
    _order = 'account_group'

    account_group = fields.Char(
        string='Group', size=4,
        help='General Account Starting Digits')
    account_type_id = fields.Many2one(
        comodel_name='account.account.type',
        string='Account Type',
        required=True)
    account_tag_ids = fields.Many2many(
        comodel_name='account.account.tag',
        relation='be_scheme_account_tag_rel',
        column1='be_scheme_id',
        column2='account_tag_id',
        string='Tags')
    report_chart_id = fields.Many2one(
        comodel_name='be.legal.financial.report.chart',
        string='Report Entry',
        ondelete='cascade')

    _sql_constraints = [
        ('group_uniq', 'unique (account_group)',
         'The General Account Group must be unique !')]
