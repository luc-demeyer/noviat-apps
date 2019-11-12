# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'ISO 20022 PAIN Support for Belgium',
    'summary': """
        This module adds Belgium-specific support to account_payment_order.""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Noviat,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-belgium',
    'depends': [
        'account_payment_order',
        'l10n_be_invoice_bba',
    ],
    'installable': True,
}
