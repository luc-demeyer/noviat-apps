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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Belgium - Multilingual Chart of Accounts (en/nl/fr)',
    'version': '8.0.1.7.4',
    'license': 'AGPL-3',
    'author': "Noviat, Odoo Community Association (OCA)",
    'website': 'http://www.noviat.com',
    'category': 'Localization/Account Charts',
    'summary': 'Belgium - Multilingual Chart of Accounts (en/nl/fr)',
    'depends': [
        'base_vat',
        'base_iban',
        'account_chart',
    ],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'data/account_account_type_nov.xml',
        'data/account_account_template_nov.xml',
        'data/account_tax_code_template_nov.xml',
        'data/account_chart_template_nov.xml',
        'data/account_tax_template_nov.xml',
        'data/account_fiscal_position_template_nov.xml',
        'data/account_fiscal_position_tax_template_nov.xml',
        'data/account_fiscal_position_account_template_nov.xml',
        'data/account_financial_report.xml',
        'data/be_legal_financial_reportscheme.xml',
        'data/l10n_be_sequence.xml',
        'views/account_menuitem.xml',
        'views/account_view.xml',
        'views/account_financial_report_view.xml',
        'views/res_config_view.xml',
        'views/l10n_be_layouts.xml',
        'views/report_financial.xml',
        'views/report_l10nbevatdeclaration.xml',
        'views/report_l10nbevatlisting.xml',
        'views/report_l10nbevatintra.xml',
        'wizard/wizard_multi_charts_accounts.xml',
        'wizard/update_be_reportscheme.xml',
        'wizard/reports.xml',
        'wizard/l10n_be_vat_declaration_view.xml',
        'wizard/l10n_be_vat_intra_view.xml',
        'wizard/l10n_be_partner_vat_listing.xml',
    ],
    'installable': True,
}
