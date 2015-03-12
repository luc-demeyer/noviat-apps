# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
#from openerp.tools.translate import _
#import logging
#_logger = logging.getLogger(__name__)


class account_tax(orm.Model):
    _inherit = 'account.tax'

    def init(self, cr):
        # replace constraint from account module
        # first check existence since 'DROP CONSTRAINT IF EXISTS' not yet supported in Postgresql 8
        cr.execute("""
            SELECT
                tc.constraint_name, tc.constraint_type, tc.table_name, kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'UNIQUE' AND  tc.table_name='account_tax' and tc.constraint_name='account_tax_name_company_uniq';
        """)
        res = cr.fetchone()
        if res:
            cr.execute('ALTER TABLE account_tax DROP CONSTRAINT account_tax_name_company_uniq;')
        cr.execute("""
            DROP INDEX IF EXISTS account_tax_name_code_unique;
            CREATE UNIQUE INDEX account_tax_name_code_unique ON account_tax (name, description, company_id) WHERE parent_id IS NULL;
        """)

    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        tax = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['description'] = (tax['description'] or '') + '(copy)'
        return super(account_tax, self).copy(cr, uid, id, default, context=context)

