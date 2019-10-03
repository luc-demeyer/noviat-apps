# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    paint_image = fields.Binary()

    @api.onchange('image')
    def _onchange_paint_image(self):
        self.paint_image = self.image
