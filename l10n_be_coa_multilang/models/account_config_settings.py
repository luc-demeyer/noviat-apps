# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.multi
    def execute(self):
        """
        Relaunch the account chart setup wizard for multi-company setups
        """
        ctx = self._context.copy()
        if self.chart_template_id \
                and self.chart_template_id.l10n_be_coa_multilang:
            module = 'l10n_be_coa_multilang'
            todo = 'wizard_multi_charts_accounts_action_todo'
            todo = self.env.ref('%s.%s' % (module, todo))
            if todo.state == 'done':
                todo.state = 'open'
            ctx.update({
                'chart_next_action': 'account.action_wizard_multi_chart',
                'chart_company_id': self.company_id.id,
                'chart_template_id': self.chart_template_id.id,
                'default_charts': 'l10n_be_coa_multilang',
            })
        return super(AccountConfigSettings, self.with_context(ctx)).execute()

    @api.multi
    def set_chart_of_accounts(self):
        """
        the accounting setup will be triggered via the todo
        cf. execute method supra
        """
        if self.chart_template_id:
            assert self.expects_chart_of_accounts \
                and not self.has_chart_of_accounts
            if self.chart_template_id.l10n_be_coa_multilang:
                return {}
        super(AccountConfigSettings, self).set_chart_of_accounts()
