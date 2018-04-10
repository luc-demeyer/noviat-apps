# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountingReport(models.TransientModel):
    _inherit = 'accounting.report'

    @api.multi
    def _build_contexts(self, data):
        result = super(AccountingReport, self)._build_contexts(data)
        account_report = self.account_report_id
        module = 'l10n_be_coa_multilang'
        refs = [
            'account_financial_report_BE_2_FULL',
            'account_financial_report_BE_3_FULL']
        be_legal_reports = [
            self.env.ref('%s.%s' % (module, ref))
            for ref in refs]
        if account_report in be_legal_reports:
            result.update({'get_children_by_sequence': True})
        return result
