# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CodaBankAccount(models.Model):
    _inherit = 'coda.bank.account'

    find_payment = fields.Boolean(
        string='Lookup Payment Reference', default=True,
        help="Invoice lookup and reconciliation via "
             "the SEPA EndToEndReference."
             "\nInstall the 'account_pain' module if you want "
             "to take advantage of this feature.")
