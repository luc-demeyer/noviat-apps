# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountTaxCodeChart(models.Model):
    """
    TODO: move to separate module.
    """
    _name = 'account.tax.code.chart'
    _description = 'Tax Tag Code Chart'
    _order = 'sequence, code'

    name = fields.Char(
        required=True, translate=True)
    code = fields.Char()
    info = fields.Text()
    parent_id = fields.Many2one(
        comodel_name='account.tax.code.chart',
        string='Parent Code', index=True)
    child_ids = fields.One2many(
        comodel_name='account.tax.code.chart',
        inverse_name='parent_id',
        string='Child Codes')
    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        help="Country for which this Chart is used")
    factor = fields.Float(
        string='Parent Coefficient',
        required=True,
        help='You can specify here the coefficient '
             'that will be used when consolidating '
             'the amount of this case into its parent. '
             'For example, set 1/-1 if you want to add/substract it.')
    invisible = fields.Boolean(
        help="Hide this entry from the report.")
    color = fields.Char(
        help="CSS color unit")
    font = fields.Selection(
        selection=lambda self: self._selection_fonts())
    sequence = fields.Integer(default=0)

    @api.model
    def _selection_fonts(self):
        return [
            ('b', 'bold'),
            ('i', 'italic'),
            ('u', 'underline'),
            ('bi', 'bold-italic'),
            ('bu', 'bold-underline'),
            ('iu', 'italic-underline'),
            ('biu', 'bold-italic-underline'),
        ]

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
