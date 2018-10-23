# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ReportAccountReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def get_account_lines(self, data):
        ctx = self.env.context.copy()
        if 'used_context' in data \
                and data['used_context'].get('get_children_by_sequence'):
            ctx.update({
                'get_children_by_sequence': True,
                'add_code_to_name': True,
            })
        lines = super(
            ReportAccountReportFinancial, self.with_context(ctx)
            ).get_account_lines(data)
        return lines
