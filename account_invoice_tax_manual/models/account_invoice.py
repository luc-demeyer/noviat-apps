# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    amount = fields.Float(help="Tax amount in invoice currency.")
    tax_amount = fields.Float(help="Tax amount in company currency.")
