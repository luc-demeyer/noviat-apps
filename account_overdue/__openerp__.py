# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Overdue Payments customisation',
    'version': '8.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Accounting & Finance',
    'depends': ['account'],
    'data': [
        'report/print_overdue_report.xml',
        'views/res_partner.xml',
        'views/report_overdue.xml',
        'views/report_overdue_style.xml',
        'views/report_overdue_layout.xml',
        'wizard/overdue_payment_wizard.xml',
    ],
}
