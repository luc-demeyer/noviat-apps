# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        help="Limit the export to the selected Product.")
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial Number',
        help="Limit the export to the selected Lot.")
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help="Limit the export to the selected Warehouse.")
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        domain=[('usage', '=', 'internal')],
        help="Limit the export to the selected Location.")
    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Owner',
        help="Limit the export to the selected stock owner.")
    package_id = fields.Many2one(
        comodel_name='stock.quant.package', string='Package')
    # product_type limited to base.group_no_one since consumables
    # are not supposed to be used for stock management purposes
    product_type = fields.Selection([
        ('product', 'Stockable Product'),
        ('consu', 'Consumable'),
        ], string='Product Type',
        default='product',
        help="Leave blank to include Stockable and Consumable products")
    product_select = fields.Selection([
        ('all', 'All Products'),
        ('select', 'Selected Products'),
        ], string='Products',
        default=lambda self: self._default_product_select())
    import_compatible = fields.Boolean(
        string='Import Compatible Export',
        help="Generate a file for use with the 'stock_level_import' module.")
    add_cost = fields.Boolean(
        string='Add cost',
        help="Product cost at Stock Level Date."
             "\nThe resulting Qty x Cost column gives an indication of the "
             "stock value at the selected date but can be different from "
             "the effective stock Valuation since product cost may vary "
             "over time.")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'stock.inventory'))

    @api.model
    def _default_product_select(self):
        if self._context.get('active_model') in ['product.product',
                                                 'product.template']:
            return 'select'
        else:
            return 'all'

    @api.multi
    def xls_export(self):
        self.ensure_one()

        warehouses = self.warehouse_id
        if not warehouses:
            warehouses = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)])
        warehouse_ids = warehouses._ids
        if self.location_id:
            warehouse = self.location_id.get_warehouse()
            if not warehouse:
                raise UserError(
                    _("No Warehouse defined for the selected "
                      "Stock Location "))
            warehouse_ids = [warehouse.id]

        report = {
            'type': 'ir.actions.report.xml',
            'report_type': 'xlsx',
            'report_name': 'stock.level.xls',
            'context': dict(self.env.context,
                            xlsx_export=True,
                            warehouse_ids=warehouse_ids),
            'datas': {'ids': [self.id]},
        }
        return report
