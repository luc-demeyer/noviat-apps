# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from datetime import datetime


class overdue_payment_wizard(models.TransientModel):
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
        ('select', 'Selected Customers'),
        ], string='Partners', required=True,
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
            raise Warning(
                _('No Data Available'),
                _('No records found for your selection!'))

        datas = {
            'report_date': report_date,
            'company_id': company_id,
            'open_moves': open_moves,
        }

        return self.env['report'].get_action(
            overdue_partners, 'account_overdue.report_overdue',
            data=datas)
