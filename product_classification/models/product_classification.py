# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductClassification(models.Model):
    _name = 'product.classification'
    _description = 'Product Classification'
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'complete_name'
    _order = 'parent_left'

    name = fields.Char(
        string='Classification', required=True)
    note = fields.Text(
        string='Description')
    complete_name = fields.Char(
        compute='_compute_complete_name',
        string='Complete Name')
    parent_id = fields.Many2one(
        comodel_name='product.classification',
        string='Parent Classification', index=True, ondelete='cascade')
    child_ids = fields.One2many(
        comodel_name='product.classification',
        inverse_name='parent_id',
        string='Child Classifications')
    parent_left = fields.Integer(
        string='Left parent', index=True)
    parent_right = fields.Integer(
        string='Right parent', index=True)
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        column1='classification_id', column2='product_tmpl_id',
        string='Partners')
    active = fields.Boolean(
        string='Active', default=True,
        help="The active field allows you to hide "
             "the classification without removing it.")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for cl in self:
            cl.complete_name = self._get_complete_name(cl)

    def _get_complete_name(self, cl):
        if cl.parent_id:
            parent_path = self._get_complete_name(cl.parent_id) + '/'
        else:
            parent_path = ''
        return parent_path + cl.name
