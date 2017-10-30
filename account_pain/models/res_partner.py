# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_direct_debit = fields.Boolean(
        string='Supplier Direct Debit',
        help="The 'Supplier Direct Debit' flag will be set "
             "by default on Supplier Invoices.")
