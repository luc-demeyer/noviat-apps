# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class l10nBeChartCommon(models.AbstractModel):
    _name = 'l10n.be.chart.common'
    _description = 'Common code for Belgian report structures'

    factor = fields.Float(
        string='Parent Coefficient',
        help="Specify here the coefficient that will be used "
             "when consolidating the amount of this entry into its parent. "
             "For example, set 1/-1 if you want to add/substract it.")
    invisible = fields.Boolean(
        help="Hide this entry from the report.")
    color = fields.Char(
        help="CSS color unit")
    font = fields.Selection(
        selection=lambda self: self._selection_font())
    sequence = fields.Integer(default=0)
    level = fields.Integer(
        compute='_compute_level', string='Level', store=True)

    @api.model
    def _selection_font(self):
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
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for entry in self:
            level = 0
            if entry.parent_id:
                level = entry.parent_id.level + 1
            entry.level = level
