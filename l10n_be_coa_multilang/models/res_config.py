# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResConfig(models.TransientModel):
    _inherit = 'res.config'

    def _next(self):
        """
        pass context values received from account.config.settings
        wizard to the todo action.
        """
        res = super(ResConfig, self)._next()
        if (self.env.context.get('chart_next_action')
                == 'account.action_wizard_multi_chart') \
                and self.env.context.get('chart_template_id'):
            ctx = res.get('context', {})
            ctx['chart_template_id'] = self.env.context['chart_template_id']
            ctx['chart_company_id'] = self.env.context['chart_company_id']
            ctx['default_charts'] = self.env.context['default_charts'],
            res['context'] = ctx
        return res
