# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OverduePaymentWizard(models.TransientModel):
    _name = 'overdue.payment.wizard'
    _description = 'Print Overdue Payments'

    partner_select = fields.Selection(
        selection=[('all', 'All Customers'),
                   ('select', 'Selected Customers')],
        string='Partners', required=True,
        default=lambda self: self._default_partner_select())
    account_select = fields.Selection(
        selection=[('receivable', 'Receivable Accounts'),
                   ('all', 'Receivable and Payable Accounts')],
        string='Selected Accounts', required=True, default='receivable')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=lambda self: self._default_company_id())

    @api.model
    def _default_partner_select(self):
        return 'select'

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id

    @api.multi
    def overdue_payment_print(self):
        report = self._context.get('report_ref')
        dom = []
        if self.partner_select == 'select':
            dom = [('id', 'in', self._context.get('active_ids', []))]
        partners = self.env['res.partner'].search(dom)
        overdue_moves = self.env['res.partner']._get_overdue_moves(
            partners.ids, company=self.company_id,
            account_select=self.account_select)
        if not overdue_moves:
            raise UserError(
                _('No overdue transactions found for your selection!'))

        overdue_partners = overdue_moves.mapped('partner_id')
        partner_ids = list(set(overdue_partners.ids))
        report = report or 'account_overdue.report_overdue'
        datas = {
            'account_select': self.account_select,
            'report_date': fields.Date.today(),
            'company_id': self.company_id.id,
        }
        return self.env['report'].get_action(
            partner_ids, report, data=datas)
