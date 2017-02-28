# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    def create(self, vals, **kwargs):
        if vals.get('payment_line_id'):
            pl_id = vals['payment_line_id']
            del vals['payment_line_id']
        else:
            pl_id = False
        absl = super(AccountBankStatementLine, self).create(vals, **kwargs)
        if pl_id:
            pl = self.env['payment.line'].browse(pl_id)
            pl.write({'bank_statement_line_id': absl.id})
        return absl
