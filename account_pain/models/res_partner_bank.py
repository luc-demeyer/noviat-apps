# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    charge_bearer = fields.Selection(
        selection=[('CRED', 'Borne By Creditor'),
                   ('DEBT', 'Borne By Debtor'),
                   ('SHAR', 'Shared'),
                   ('SLEV', 'Following Service Level')],
        string='Charge Bearer',
        default='SLEV',
        help="Specifies which party/parties will bear the charges linked "
             "to the processing of the payment transaction.")
