# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
    'name': 'Belgium - Multilingual Chart of Accounts (en/nl/fr)',
    'version': '3.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category' : 'Localization/Account Charts',
    'description': """

    Belgian localisation (on top of l10n_be):
    * Multilanguage support (en/nl/fr) for Chart of Accounts, Taxes, Tax Codes and Journals
    * Multilingual accounting templates
    * Multilanguage support Analytic Chart of Accounts and Analytic Journals
    * Update partner titles for commonly used legal entities
    * Add constraint to ensure unique Tax Code per Company
    * Auto-select correct financial report entry when creating/changing a general account
    * Setup wizard changes
        - Copy translations for CoA, Tax, Tax Code and Fiscal Position from templates to target objects
        - Add options to install the nl and fr languages during the setup
    """,
    'depends': ['account_accountant','l10n_be','account_cancel'],
    'init_xml': [
        'belgium_base_data.xml',
    ],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'account_view.xml',        
        'account_menuitem.xml',   
        'account_account_type_nov.xml',
        'account_account_template_nov.xml',
        'account_tax_code_template_nov.xml',
        'account_chart_template_nov.xml',
        'account_tax_template_nov.xml',
        'account_fiscal_position_template_nov.xml',
        'account_fiscal_position_tax_template_nov.xml',
        'account_fiscal_position_account_template_nov.xml',
        'wizard_multi_charts_accounts.xml',
        'account_financial_report.xml',
        'be_legal_financial_reportscheme.xml',
        'account_financial_report_view.xml',
        'update_be_reportscheme.xml',
        # l10n_be wizards
        'wizard/l10n_be_vat_declaration_view.xml',
        'wizard/l10n_be_partner_vat_listing.xml',
    ],
    'active': False,
    'installable': True,}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
