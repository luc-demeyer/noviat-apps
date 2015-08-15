# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
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

{
    'name': 'Belgium - Advanced CODA statements Import',
    'version': '0.6',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'Belgium - Advanced CODA statements Import',
    'depends': [
        'base_iban',
        'l10n_be_invoice_bba',
        'l10n_be_partner',
        'account_bank_statement_advanced',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/account_coda_trans_type.xml',
        'data/account_coda_trans_code.xml',
        'data/account_coda_trans_category.xml',
        'data/account_coda_comm_type.xml',
        'views/account_bank_statement.xml',
        'views/account_coda.xml',
        'views/account_coda_comm_type.xml',
        'views/account_coda_trans_category.xml',
        'views/account_coda_trans_code.xml',
        'views/account_coda_trans_type.xml',
        'views/coda_bank_account.xml',
        'views/coda_bank_statement.xml',
        'views/menuitem.xml',
        'wizard/coda_import_wizard.xml',
        ],
    'installable': True,
}
