# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class CodaAccountMappingRule(models.Model):
    _inherit = 'coda.account.mapping.rule'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product', index=True)
    reinvoice_key_id = fields.Many2one(
        comodel_name='account.reinvoice.key',
        string='Reinvoice Key', index=True)

    def _rule_select_extra(self, coda_bank_account_id):
        res = super(CodaAccountMappingRule, self)._rule_select_extra(
            coda_bank_account_id)
        return res + ', product_id, reinvoice_key_id'

    def _rule_result_extra(self, coda_bank_account_id):
        res = super(CodaAccountMappingRule, self)._rule_result_extra(
            coda_bank_account_id)
        return res + ['product_id', 'reinvoice_key_id']
