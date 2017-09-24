# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Batch Reinvoice Service',
    'version': '8.0.0.2.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Batch Reinvoice Service',
    'depends': [
        'account_reinvoice',
    ],
    'data': [
        'security/account_reinvoice_batch.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/account_reinvoice_batch_log.xml',
    ],
    'installable': True,
}
