# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line XLSX export',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'category': 'Accounting & Finance',
    'summary': 'Journal Items Excel export',
    'depends': ['account', 'report_xlsx_helper'],
    'data': [
        'report/account_move_line_xlsx.xml',
    ],
    'installable': True,
}
