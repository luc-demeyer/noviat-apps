# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
        ctx = self.env.context
        report = ctx.get('ref_report_action') \
            or 'account_overdue.report_print_overdue_action'
        data = {
            'partner_ids': ctx.get('active_ids'),
            'wiz_id': self.id,
        }
        return self.env.ref(report).report_action(self, data=data)
