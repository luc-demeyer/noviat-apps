# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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


class account_bank_statement(orm.Model):
    _inherit = 'account.bank.statement'
    _columns = {
        'coda_id': fields.many2one(
            'account.coda', 'CODA Data File', ondelete='cascade'),
        'fiscalyear_id': fields.related(
            'period_id', 'fiscalyear_id', type='many2one',
            relation='account.fiscalyear', string='Fiscal Year',
            store=True, readonly=True),
        'coda_note': fields.text('CODA Notes'),
    }

    def init(self, cr):
        cr.execute("""
    ALTER TABLE account_bank_statement
      DROP CONSTRAINT IF EXISTS account_bank_statement_name_uniq;
    DROP INDEX IF EXISTS account_bank_statement_name_non_slash_uniq;
    CREATE UNIQUE INDEX account_bank_statement_name_non_slash_uniq ON
      account_bank_statement(name, journal_id, fiscalyear_id, company_id)
      WHERE name !='/';
        """)
