# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class OverduePaymentWizard(models.TransientModel):
    _name = 'overdue.payment.wizard'
    _description = 'Print Overdue Payments'

    def init(self, cr):
        """
        disable standard overdue print
        """
        cr.execute(
            "UPDATE ir_values "
            "SET key2='#client_print_multi' "
            "WHERE name='Due Payments' "
            "AND model='res.partner' "
            "AND value LIKE 'ir.actions.report.xml,%' "
            "AND key2='client_print_multi';")

    partner_select = fields.Selection([
        ('all', 'All Customers'),
        ('select', 'Selected Customers')],
        string='Partners', required=True,
        default=lambda self: self._default_partner_select())
    account_select = fields.Selection([
        ('receivable', 'Receivable Accounts'),
        ('all', 'Receivable and Payable Accounts')],
        string='Selected Accounts', required=True, default='receivable')
    # company_id not on UI in the current release of this module
    # user needs to switch to new company to send overdue letters
    # in multi-company environment
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self._default_company())

    @api.model
    def _default_partner_select(self):
        return 'select'

    @api.model
    def _default_company(self):
        return self.env.user.company_id

    @api.multi
    def overdue_payment_print(self):
        report = self._context.get('report_ref')
        company_id = self.company_id.id
        partner_select = self.partner_select
        account_select = self.account_select
        partner_mod = self.env['res.partner']

        report_date = fields.Datetime.context_timestamp(
            self, datetime.now()).date()
        report_date = report_date.strftime('%Y-%m-%d')
        if partner_select == 'select':
            partner_ids = self._context.get('active_ids', [])
        else:
            partner_ids = [x.id for x in partner_mod.search([])]
        overdue_partners, open_moves = partner_mod._get_overdue_partners(
            report_date, company_id, partner_ids, account_select)
        if not overdue_partners:
            raise UserError(
                _('No Data Available'),
                _('No records found for your selection!'))

        datas = {
            'report_date': report_date,
            'company_id': company_id,
            'open_moves': open_moves,
        }

        report = report or 'account_overdue.report_overdue'
        return self.env['report'].get_action(
            overdue_partners, report, data=datas)
