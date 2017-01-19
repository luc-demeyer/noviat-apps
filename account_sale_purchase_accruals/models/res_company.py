# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    accrual_journal_id = fields.Many2one(
        'account.journal',
        string='Accrual Journal',
        help="Financial Journal used for the Accrual Entries for "
             "the Sale, Stock and Purchase processes.")
