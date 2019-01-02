# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class account_chart_template(models.Model):
    _inherit = 'account.chart.template'
    _order = 'name'

    name = fields.Char(translate=True)
    l10n_be_coa_multilang = fields.Boolean(string='Multilang Belgian CoA')
