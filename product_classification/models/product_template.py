# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    classification_ids = fields.Many2many(
        comodel_name='product.classification',
        column1='product_tmpl_id',
        column2='classification_id',
        string='Product Classification')
