# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CodaAccountMappingRule(models.Model):
    _inherit = 'coda.account.mapping.rule'

    split = fields.Boolean(
        help="Split line into two separate lines with "
             "transaction amount and transaction cost.")
    # free form communication parsing fields
    transaction_amount_pos = fields.Char(
        string='Amount Position',
        help="Specify the string preceding the position in the "
             "free form Communication containing the transaction amount "
             "and the length of the amount string."
             "\nSyntax: string, length"
             "e.g. BRT:, 10")
    transaction_cost_pos = fields.Char(
        string='Cost Position',
        help="Specify the string preceding the position in the "
             "free form Communication containing the transaction cost "
             "and the length of the cost string."
             "\nSyntax: string, length"
             "e.g. C:, 8")
    # cost line transaction signature fields
    cost_trans_code_id = fields.Many2one(
        comodel_name='account.coda.trans.code',
        string='Cost Transaction Code',
        domain=[('type', '=', 'code')])
    cost_trans_category_id = fields.Many2one(
        comodel_name='account.coda.trans.category',
        string='Cost Transaction Category')
