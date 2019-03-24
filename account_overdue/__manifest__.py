# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Overdue Payments customisation',
    'version': '10.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'depends': ['account'],
    'data': [
        'report/print_overdue_report.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/report_overdue.xml',
        'views/report_overdue_style.xml',
        'views/report_overdue_layout.xml',
        'wizard/overdue_payment_wizard.xml',
    ],
    'installable': True,
    'pre_init_hook': 'disable_action_report_print_overdue',
}
