# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CODA Import - Handle Payment Card Cost',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'summary': 'CODA Import - Handle Payment Card Cost',
    'depends': [
        'l10n_be_coda_advanced',
    ],
    'data': [
        'views/coda_bank_account_views.xml',
    ],
    'installable': True,
}
