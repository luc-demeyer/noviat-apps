# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
    'name': 'Bank Statement extensions to support e-banking',
    'version': '2.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category': 'Generic Modules/Accounting',
    'description': """
Bank Statement extensions
=========================

This module extends the standard account_bank_statement_line object for
better scalability and e-banking support.

This module adds:
-----------------
- valuta date
- batch payments
- Payment Reference field to support ISO 20022 EndToEndReference
  (simple or batch. detail) or PaymentInformationIdentification (batch)
- Creditor Reference fields to support ISO 20022 CdtrRefInf
  (e.g. structured communication & communication type)
- traceability of changes to bank statement lines
- bank statement line views
- bank statements balances report
- performance improvements for digital import of bank statement
  (via 'ebanking_import' context flag)
- name_search on res.partner.bank enhanced to allow search on bank
  and iban account numbers
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'account_bank_statement_view.xml',
        'wizard/bank_statement_balance_print.xml',
        'data/account_bank_statement_extensions_data.xml',
    ],
    'auto_install': False,
    'installable': True,
}
