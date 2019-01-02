# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountCommonReport(models.TransientModel):
    _inherit = 'account.common.report'

    def _build_contexts(self, data):
        """
        No date_from for balance sheet if we select a fiscal year.
        """
        result = super(AccountCommonReport, self)._build_contexts(data)
        if self.date_range_id.type_id.fiscal_year:
            module = __name__.split('addons.')[1].split('.')[0]
            be_bs = self.env.ref(
                '%s.account_financial_report_BE_2_FULL' % module)
            if self.account_report_id == be_bs:
                result['date_from'] = False
        return result

    @api.multi
    def check_report(self):
        res = super(AccountCommonReport, self).check_report()
        if self.date_range_id.type_id.fiscal_year:
            module = __name__.split('addons.')[1].split('.')[0]
            be_bs = self.env.ref(
                '%s.account_financial_report_BE_2_FULL' % module)
            be_pl = self.env.ref(
                '%s.account_financial_report_BE_3_FULL' % module)
            if self.account_report_id in [be_bs, be_pl]:
                report = res['data']['form']['account_report_id']
                report = (report[0],
                          ' - '.join([report[1], self.date_range_id.name]))
                res['data']['form']['account_report_id'] = report
        return res
