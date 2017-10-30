# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        pl = False
        if vals.get('payment_reference'):
            pls = self.env['payment.line'].search(
                [('name', '=', vals['payment_reference'])])
            if len(pls) == 1:
                pl = pls[0]
        absl = super(AccountBankStatementLine, self).create(vals)
        if pl:
            pl.write({'bank_statement_line_id': absl.id})
        return absl
