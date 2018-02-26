# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from openerp import api, fields, models


class WizPartnerOpenArapPeriod(models.TransientModel):
    _name = 'wiz.partner.open.arap.period'
    _description = 'Open Receivables/Payables by Period'

    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Period', required=True,
        default=lambda self: self._default_period_id())
    target_move = fields.Selection(
        selection=[('posted', 'All Posted Entries'),
                   ('all', 'All Entries')],
        string='Target Moves', default='posted', required=True)
    result_selection = fields.Selection(
        selection=[('customer', 'Receivable Accounts'),
                   ('supplier', 'Payable Accounts'),
                   ('customer_supplier', 'Receivable and Payable Accounts')],
        string='Filter on', default='customer', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        domain=[('parent_id', '=', False)],
        string='Partner',
        help="Leave blank to select all partners.")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', readonly=True,
        default=lambda self: self._default_company_id())

    @api.model
    def _default_period_id(self):
        now = time.strftime('%Y-%m-%d')
        periods = self.env['account.period'].search(
            [('date_start', '<=', now),
             ('date_stop', '>=', now)],
            limit=1)
        return periods and periods[0]

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.account')

    @api.multi
    def print_report(self):
        self.ensure_one()
        ctx = self._context.copy()
        if ctx.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'account.partner.open.arap.period.xls'}
        else:
            ctx['landscape'] = True
            return self.env['report'].with_context(ctx).get_action(
                self,
                'account_open_receivables_payables_xls.report_open_arap')

    @api.multi
    def xls_export(self):
        self.ensure_one()
        return self.print_report()
