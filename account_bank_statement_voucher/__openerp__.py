# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
    'name': 'OpenERP account_bank_statement/account_voucher usability improvements',
    'version': '2.2',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category' : 'Generic Modules/Accounting',
    'description': """
    
    Usability improvements when using account_voucher in combination with bank_statement processing :
    - Generate & maintain accounting moves from within a bank statement on a line by line basis. 
    - Replace the "F1/F2 create/open voucher" function keys by buttons.
    - For AR/AP general accounts the account_voucher object is used for reconciliation, for other accounts a regular move is created.
    - An intermediate selection screen is presented in case of multiple outstanding invoicces. This screen is pre-filled with the matching line(s). 
    - Bank statement line buttons : the green arrow creates/opens Voucher or Move, the Delete button removes draft Vouchers or Moves.
    - The reconciled amount is shown on the bank statement line. An exclamation mark indicates differences between the paid amount and the open transactions.
    - The possibility to delete a Bank Statement with associated Posted Vouchers or Moves has been disabled.
    - Tax Codes and Tax Base Amounts can be added to the generated Accounting Moves in order to facilitate the encoding of bank costs.
    - The Bank Statement Confirm behaviour has been changed: at Confirm time a Posted Move will be created for Bank Statement Lines with no or Draft Moves.
    - Accounting Entry Changes are blocked for Moves linked to a Confirmed Bank Statement. 
    - The creation of Payment Voucher on Confirmed Bank Statements is not allowed.
    - Invoices associated to Vouchers are re-opened automatically hen unreconciling a Posted Vouchers.
    - Otherwise 'orphaned' Voucher Lines are removed when the associated Accounting Entry Line is deleted.
    - Remove Vouchers created from an invoice (e.g. via invoice 'Payment' button) when the invoice is cancelled.
    - Remove Vouchers created from a bank statement line when the Voucher reference is removed from the bank statement line.
    - Generate Statement Line sequence number at Line creation time (in stead of at Bank Statement Write).
    - Generate Voucher number and Move name from bank statement number and line.
    - Update Partner records with Bank Account Number information during reconciliation (including BBAN->IBAN conversion).
    """,
    'depends': ['account', 'account_voucher'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml' : [
        'security/ir.model.access.csv',
        'account_voucher_view.xml',
        'account_bank_statement_view.xml',
        'account_move_view.xml',
        'wizard/account_voucher_create_view.xml',
        'wizard/account_move_create_view.xml',
        'wizard/update_partner_record.xml',
    ],
    'active': False,
    'installable': True,}
