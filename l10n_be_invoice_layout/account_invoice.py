# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_print(self):
        """
        We replace the return action by report_be_invoice.
        Remark:
        The approach of replacing the account.account_invoices
        report definition by the Belgian layout needs to be adapted
        if different templates are required (e.g. to support
        multi-country/multi-company setups).
        """
        assert len(self) == 1, \
            'This option should only be used for a single id at a time.'
        self.sent = True
        return self.env['report'].get_action(
            self, 'l10n_be_invoice_layout.report_be_invoice')
