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
    'name': 'Belgium - Invoices with Structured Communication',
    'version': '1.7',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'website': 'http://www.noviat.com',
    'category': 'Localization',
    'description': """
Belgian Structured Communication for invoices
=============================================

This module adds support for the Belgian Structured Communication on in- and
outgoing invoices as follows:

    * The 'Reference' field label on an invoice is renamed to 'Communication'.
    * A Structured Communication can be generated automatically on outgoing
      invoices according to a number of algorithms.
    * The preferred type of Structured Communication and associated algorithm
      can be specified on the Partner records.
      A 'random' Structured Communication will be generated if no algorithm is
      specified on the Partner record.

Supported algorithms for outgoing invoices
------------------------------------------

    1) Random: **+++RRR/RRRR/RRRDD+++**

       **R..R** = Random Digits, **DD** = Check Digits

    2) Date: **+++DOY/YEAR/SSSDD+++**

       **DOY** = Day of the Year, **SSS** = Sequence Number, **DD** = Check Digits

    3) Customer Reference: **+++RRR/RRRR/SSSDDD+++**

       **R..R** = Customer Reference without non-numeric characters,
       **SSS** = Sequence Number, **DD** = Check Digits

    """,
    'depends': [
        'account',
    ],
    'data': [
        'partner_view.xml',
        'account_invoice_view.xml',
    ],
    'images': [
        'images/invoice.jpg',
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
