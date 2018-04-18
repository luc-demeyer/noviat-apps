# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class res_company(models.Model):
    _inherit = 'res.company'

    in_inv_cd_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Incoming Invoice Cash Discount Account',
        domain=[('deprecated', '=', False)],
        help="Default Cash Discount Account on incoming Invoices."
             "This field will only be used for invoices subject "
             "to the belgian cash discount regulation.")
    out_inv_cd_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Outgoing Invoice Cash Discount Account',
        domain=[('deprecated', '=', False)],
        help="Default Cash Discount Account on outgoing Invoices."
             "This field will only be used for invoices subject "
             "to the belgian cash discount regulation.")
    out_inv_cd_term = fields.Integer(
        string='Outgoing Invoice Cash Discount Term',
        help="Default Cash Discount Term (in days) on outgoing Invoices."
             "This field will only be used for invoices subject "
             "to the belgian cash discount regulation.")
