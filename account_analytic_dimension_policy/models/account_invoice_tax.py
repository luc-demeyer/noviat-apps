# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    analytic_dimension_policy = fields.Selection(
        string='Policy for analytic dimension',
        related='account_id.analytic_dimension_policy', readonly=True)
    invoice_state = fields.Selection(
        string='Invoice State',
        default='draft',
        related='invoice_id.state', readonly=True)
