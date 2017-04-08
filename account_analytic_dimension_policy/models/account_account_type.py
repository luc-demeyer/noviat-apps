# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# ----------------------------------------------------------------------------
#    Inspired by account_analytic_required module from
#    Alexis de Lattre <alexis.delattre@akretion.com>

from openerp import api, fields, models, _


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    analytic_dimension_policy = fields.Selection(
        '_get_policies', string='Policy for analytic dimension',
        required=True, default=lambda self: self._default_policy())

    @api.model
    def _get_policies(self):
        return [('optional', _('Optional')),
                ('always', _('Always')),
                ('never', _('Never'))]

    @api.model
    def _default_policy(self):
        return 'optional'

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type in ['none', 'asset', 'liabilty']:
            self.analytic_dimension_policy = 'never'
        else:
            self.analytic_dimension_policy = 'optional'
