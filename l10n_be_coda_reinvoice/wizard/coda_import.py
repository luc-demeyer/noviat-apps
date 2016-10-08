# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from openerp import models


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _prepare_mv_line_dict(self, coda_statement, line):
        mv_line_dict = super(AccountCodaImport, self)._prepare_mv_line_dict(
            coda_statement, line)
        if line.get('reinvoice_key_id'):
            mv_line_dict['reinvoice_key_id'] = line['reinvoice_key_id']
        if line.get('product_id'):
            mv_line_dict['product_id'] = line['product_id']
        return mv_line_dict
