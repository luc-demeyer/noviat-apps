# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for OpenERP
#    Copyright (C) 2004-2009 Tiny SPRL (http://tiny.be)
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp.osv import orm, fields


class report_intrastat_code(orm.Model):
    _name = "report.intrastat.code"
    _description = "H.S. Code"
    _order = "name"

    _columns = {
        'name': fields.char(
            'H.S. code', size=16,
            help="Full length Harmonized System code (digits only). "
            "Full list is available from the World Customs Organisation, "
            "see http://www.wcoomd.org"),
        'description': fields.char(
            'Description', size=255,
            help='Short text description of the H.S. category'),
        'intrastat_code': fields.char(
            'Intrastat CN code', size=9, required=True,
            help="Code used for the Intrastat declaration. Must be part "
            "of the 'Combined Nomenclature' (CN) with 8 digits with "
            "sometimes a 9th digit."),
        'intrastat_uom_id': fields.many2one(
            'product.uom', 'UoM for intrastat product report',
            help="Select the unit of measure if one is required for "
            "this particular Intrastat Code (other than the weight in Kg). "
            "If no particular unit of measure is required, leave empty."),
    }

    def _hs_code(self, cr, uid, ids):
        for code_to_check in self.read(cr, uid, ids, ['name']):
            if code_to_check['name']:
                if not code_to_check['name'].isdigit():
                    return False
        return True

    def _cn_code(self, cr, uid, ids):
        for code_to_check in self.read(cr, uid, ids, ['intrastat_code']):
            if code_to_check['intrastat_code']:
                if (not code_to_check['intrastat_code'].isdigit()
                        or len(code_to_check['intrastat_code'])
                        not in (8, 9)):
                    return False
        return True

    _constraints = [
        (_hs_code,
         "The 'Harmonised System Code' should only contain digits.",
         ['name']),
        (_cn_code,
         "The 'Intrastat CN Code' should have exactly 8 or 9 digits.",
         ['intrastat_code']),
    ]

    _sql_constraints = [
        ('hs_code_uniq', 'unique(name)',
         'This H.S. code already exists !'),
        ('intrastat_code_uniq', 'unique(intrastat_code)',
         'This Intrastat code already exists !'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for code in self.browse(cr, uid, ids, context=context):
            name = code.name or code.intrastat_code
            if code.description:
                name = u'%s %s' % (name, code.description)
            res.append((code.id, name))
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('intrastat_code'):
            vals['intrastat_code'] = vals['intrastat_code'].replace(' ', '')
        return super(report_intrastat_code, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if ids and vals.get('intrastat_code'):
            vals['intrastat_code'] = vals['intrastat_code'].replace(' ', '')
        return super(report_intrastat_code, self).write(
            cr, uid, ids, vals, context=context)


class product_template(orm.Model):
    _inherit = "product.template"

    _columns = {
        'intrastat_id': fields.many2one(
            'report.intrastat.code', 'Intrastat Code',
            help="Code from the Harmonised System. Nomenclature is "
            "available from the World Customs Organisation, see "
            "http://www.wcoomd.org/. Some countries have made their own "
            "extensions to this nomenclature."),
    }


class product_category(orm.Model):
    _inherit = "product.category"

    _columns = {
        'intrastat_id': fields.many2one(
            'report.intrastat.code', 'Intrastat Code',
            help="Code from the Harmonised System. If this code is not "
            "set on the product itself, it will be read here, on the "
            "related product category."),
    }
