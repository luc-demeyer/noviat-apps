# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class EbicsFileFormat(models.Model):
    _name = 'ebics.file.format'
    _description = 'EBICS File Formats'
    _order = 'type,name'

    name = fields.Char(string='Name', required=True)
    type = fields.Selection(
        selection=[('ful', 'Upload'),
                   ('fdl', 'Download')],
        required=True)
    description = fields.Char()
    suffix = fields.Char(
        required=True,
        help="Specify the filename suffix for this File Format."
             "\nE.g. camt.053.xml")
