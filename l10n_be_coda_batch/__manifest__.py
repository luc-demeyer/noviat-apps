# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Belgium - CODA statements batch import',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'CODA statements batch import',
    'depends': ['l10n_be_coda_advanced'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_coda_batch_log.xml',
        'views/res_company.xml',
        'wizard/account_coda_batch_import.xml'
    ],
    'installable': True,
}
