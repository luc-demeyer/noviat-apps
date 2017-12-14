# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class EbicsFileFormat(models.Model):
    _name = 'ebics.file.format'
    _description = 'EBICS File Formats'
    _order = 'type,name'

    name = fields.Char(string='Request Type', required=True)
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
        up = self._supported_upload_order_types()
        down = self._supported_download_order_types()
        selection = [(x, x) for x in up + down]
        return selection

    def _supported_upload_order_types(self):
        return ['FUL', 'CCT']

    def _supported_download_order_types(self):
        return ['FDL', 'C53']
