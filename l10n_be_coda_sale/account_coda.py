# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2010-now Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields


class coda_bank_account(models.Model):
    _inherit = 'coda.bank.account'

    find_so_number = fields.Boolean(
        string='Lookup Sales Order Number', default=True,
        help="Partner lookup and reconciliation via the Sales Order "
             "when a communication in free format is used."
             "\nA reconciliation will only be created in case of exact match "
             "between the Sales Order Invoice and Bank Transaction amounts.")
