# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountPainCreate(models.TransientModel):
    _name = 'account.pain.create'
    _description = 'ISO 20022 payment file'

    pain_data = fields.Binary(
        string='Payment File', required=True, readonly=True)
    pain_fname = fields.Char(
        string='Filename', size=128, required=True)
    note = fields.Text(string='Remarks')
