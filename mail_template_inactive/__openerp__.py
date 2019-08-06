# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Email Template Inactive',
    'summary': 'Add active flag to Email Templates',
    'author': 'Noviat',
    'category': 'Mail',
    'website': 'https://www.noviat.com',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'email_template',
    ],
    'data': [
        'views/mail_template.xml',
    ],
    'installable': True,
}
