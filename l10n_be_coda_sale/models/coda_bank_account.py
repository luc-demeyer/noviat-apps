# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class CodaBankAccount(models.Model):
    _inherit = 'coda.bank.account'

    find_so_number = fields.Boolean(
        string='Lookup Sales Order Number', default=True,
        help="Partner lookup and reconciliation via the Sales Order "
             "when a communication in free format is used."
             "\nA reconciliation will only be created in case of exact match "
             "between the Sales Order Invoice and Bank Transaction amounts.")
