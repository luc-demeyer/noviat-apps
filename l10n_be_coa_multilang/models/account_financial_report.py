# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'

    code = fields.Char(size=16)
    invisible = fields.Boolean(
        help="Hide this entry from the printed report.")

    def _convert_to_cache(self, values, update=False, validate=True):
        """
        The 'report.account.report_financial, get_account_lines' method
        does not allow to include extra fields in list of returned
        value dicts.
        We bypass this limitation by adding the 'code' to the 'name'
        field for the belgian reports.

        TODO:
        make PR to add an '_update_account_lines' method into the
        get_account_lines method so that this code can be replaced
        by a cleaner solution.
        """
        res = super(AccountFinancialReport, self)._convert_to_cache(
            values, update=update, validate=validate)
        if self.env.context.get('add_code_to_name') \
                and res.get('code') and res.get('name'):
            res['name'] += ' - (' + res['code'] + ')'
        return res

    def _get_children_by_order(self):
        if self.env.context.get('get_children_by_sequence'):
            res = self.search(
                [('id', 'child_of', self.ids[0]), ('invisible', '=', 0)],
                order='sequence ASC')
        else:
            res = super(
                AccountFinancialReport, self)._get_children_by_order()
        return res
