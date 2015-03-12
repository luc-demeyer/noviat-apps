# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012-14 Agaplan (www.agaplan.eu) & Noviat (www.noviat.com).
#    All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    _columns = {
        'intrastat_declare': fields.boolean('Declare for intrastat'),
        'intrastat_country_id': fields.many2one(
            'res.country', 'Intrastat country',
            help="Used to override the country on the partner address, "
            "leave empty to use default from partner address"),
    }

    _defaults = {
        'intrastat_declare': True,
    }


class stock_move(orm.Model):
    _inherit = 'stock.move'

    _columns = {
        'intrastat_declare': fields.boolean('Declare for intrastat'),
        'intrastat_transaction': fields.integer('Intrastat transaction type'),
        'intrastat_weight': fields.char(
            'Intrastat Weight', size=16,
            help="This overrides the total weight for this intrastat line, "
            "leave empty to use product netto weight * qty."),
        'intrastat_qty': fields.char(
            'Intrastat Qty', size=16,
            help="Overrides the qty declared on intrastat, "
            "leave empty to use the qty on the stock move."),
    }

    _defaults = {
        'intrastat_declare': True,
    }
