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


class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'intrastat_belgium': fields.boolean(
            'Do a Belgian Intrastat declaration for this company'),
        'intrastat_belgium_region': fields.selection([
            (1, '1. Flemish Region'),
            (2, '2. Walloon Region'),
            (3, '3. Brussels-Capital Region'),
            ], string='Region', required=True),
        'data_source': fields.selection([
            ('move', 'Generate report from Stock Moves'),
            ('invoice', 'Generate report from Invoices'),
            ], string='Report Data Source', required=True),
        'intrastat_belgium_arrival': fields.boolean(
            'Arrival Declaration',
            help="Is this company required to send arrival declarations ?"),
        'intrastat_belgium_departure': fields.boolean(
            'Departure Declaration',
            help="Is this company required to send departure declarations ?"),
        'intrastat_belgium_arrival_extended': fields.boolean(
            'Extended Arrival Declaration',
            help="Does this company require "
            "an extended arrival declaration ?"),
        'intrastat_belgium_departure_extended': fields.boolean(
            'Extended Departure Declaration',
            help="Does this company require "
            "an extended departure declaration ?"),
    }

    _defaults = {
        'data_source': 'invoice',
    }
