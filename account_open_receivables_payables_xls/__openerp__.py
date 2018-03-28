# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Open Receivables/Payables XLS export',
    'version': '8.0.2.2.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Open Receivables/Payables XLS export',
    'depends': ['account', 'report_xls'],
    'data': [
        'views/arap_layouts.xml',
        'views/report_open_arap.xml',
        'wizard/wiz_partner_open_arap_period.xml',
        'report/report.xml',
    ],
    'installable': True,
}
