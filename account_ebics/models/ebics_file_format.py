# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class EbicsFileFormat(models.Model):
    _name = 'ebics.file.format'
    _description = 'EBICS File Formats'
    _order = 'type,name'

    name = fields.Char(string='Name', required=True)
    type = fields.Selection(
        selection=[('down', 'Download'),
                   ('up', 'Upload')],
        required=True)
    order_type = fields.Selection(
        selection=lambda self: self._selection_order_type(),
        string='Order Type',
        help="For most banks is France you should use the "
             "format neutral Order Types 'FUL' for upload "
             "and 'FDL' for download.")
    description = fields.Char()
    suffix = fields.Char(
        required=True,
        help="Specify the filename suffix for this File Format."
             "\nE.g. camt.053.xml")

    @api.model
    def _selection_order_type(self):
        return[
            ('FUL', 'FUL'),
            ('FDL', 'FDL'),
            ('CCT', 'CCT'),
        ]
