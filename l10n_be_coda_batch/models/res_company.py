# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    coda_batch_root = fields.Char(
        string='CODA Batch Root',
        default=lambda self: self._default_batch_root(),
        help="Root Directory for CODA Batch Folders.")

    @api.model
    def _default_batch_root(self):
        return '/'.join(['/home/odoo/coda_batch_root', self.env.cr.dbname])
