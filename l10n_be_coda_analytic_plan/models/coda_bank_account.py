# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class CodaAccountMappingRule(models.Model):
    _inherit = 'coda.account.mapping.rule'

    analytics_id = fields.Many2one(
        'account.analytic.plan.instance', string='Analytic Distribution')

    def _rule_select_extra(self, coda_bank_account_id):
        return ', analytics_id'

    def _rule_result_extra(self, coda_bank_account_id):
        return ['analytics_id']
