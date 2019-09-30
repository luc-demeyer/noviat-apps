# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'
    _order = 'name'

    name = fields.Char(translate=True)
    l10n_be_coa_multilang = fields.Boolean(string='Multilang Belgian CoA')

    def get_countries_posting_at_bank_rec(self):
        rslt = super(
            AccountChartTemplate, self
            ).get_countries_posting_at_bank_rec()
        rslt.append('BE')
        return rslt
