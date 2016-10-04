# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class WizExportStockLevel(models.TransientModel):
    _name = 'wiz.export.stock.level'
    _description = 'Generate a stock level report for a given date'

    stock_level_date = fields.Datetime(
        string='Stock Level Date',
        help="Specify the Date & Time for the Stock Levels."
             "\nThe current stock level will be given if not specified.")
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        help="Limit the export to the selected Product Category.")
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help="Limit the export to the selected Warehouse.")
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        help="Limit the export to the selected Location. "
             "Child locactions will be included as well.")
    product_select = fields.Selection([
        ('all', 'All Products'),
        ('select', 'Selected Products'),
        ], string='Products',
        default=lambda self: self._default_product_select())
    import_compatible = fields.Boolean(
        string='Import Compatible Export',
        help="Generate a file for use with the 'stock_level_import' module.")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'stock.inventory'))

    def _default_product_select(self):
        if self._context.get('active_model') in ['product.product',
                                                 'product.template']:
            return 'select'
        else:
            return 'all'

    @api.onchange('import_compatible')
    def _onchange_import_compatible(self):
        dom = [('company_id', '=', self.company_id.id)]
        self.warehouse_id = False
        if self.import_compatible:
            dom2 = [('usage', '=', 'internal')]
        else:
            dom2 = [('usage', 'in', ['view', 'internal'])]
        domain = dom + dom2
        return {'domain': {'location_id': domain}}

    def _xls_export_domain(self):
        ctx = self._context
        domain = [
            ('type', 'in', ['product', 'consu']),
            '|', ('active', '!=', 'True'), ('active', '=', 'True'),
            '|', ('company_id', '=', self.company_id.id),
            ('company_id', '=', False)
        ]
        if self.categ_id:
            domain.append(('categ_id', 'child_of', self.categ_id.id))
        if self.product_select == 'select':
            if ctx.get('active_model') == 'product.product':
                domain.append(('id', 'in', ctx.get('active_ids')))
            elif ctx.get('active_model') == 'product.template':
                products = self.env['product.product'].search(
                    [('product_tmpl_id', 'in', ctx.get('active_ids'))])
                domain.append(('id', 'in', products._ids))
        return domain

    def _update_datas(self, datas):
        """
        Update datas when adding extra options to the wizard
        in inherited modules.
        """
        pass

    @api.multi
    def xls_export(self):
        self.ensure_one()
        warehouses = self.warehouse_id
        if not warehouses:
            warehouses = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)])
        domain = self._xls_export_domain()
        products = self.env['product.product'].search(domain)
        if not products:
            raise UserError(
                _("No Data Available."),
                _("'\nNo records found for your selection !"))

        if self.location_id:
            loc_domain = [
                ('location_id', 'child_of', [self.location_id.id]),
                ('usage', '=', 'internal')]
            locations = self.env['stock.location'].search(loc_domain)
            if locations:
                location_ids = locations._ids
            else:
                raise UserError(
                    _("No Data Available."),
                    _("\nNo physical stock locations defined "
                      "for your selection !"))
        else:
            location_ids = []

        datas = {
            'model': self._name,
            'stock_level_date':
                self.import_compatible
                and False or self.stock_level_date,
            'product_ids': products._ids,
            'category_id': self.categ_id.id,
            'warehouse_ids': warehouses._ids,
            'location_ids': location_ids,
            'product_select': self.product_select,
            'import_compatible': self.import_compatible,
            'company_id': self.company_id.id,
        }
        self._update_datas(datas)
        return {'type': 'ir.actions.report.xml',
                'report_name': 'stock.level.xls',
                'datas': datas}
