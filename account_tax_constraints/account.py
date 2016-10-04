# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, _
from openerp.exceptions import Warning


class account_tax(models.Model):
    _inherit = 'account.tax'

    def unlink(self, cr, uid, ids, context=None):
        for tax_id in ids:
            cr.execute(
                "SELECT tax_id FROM account_invoice_line_tax "
                "WHERE tax_id=%s LIMIT 1",
                (tax_id,))
            res = cr.fetchone()
            if res:
                raise Warning(_(
                    "Invalid action !"
                    "\nYou cannot delete a Tax Object "
                    "that is linked to an Invoice line !"
                    "\nAs an alternative, you can disable "
                    "Tax Objects via the 'Active' flag."))
        return super(account_tax, self).unlink(
            cr, uid, ids, context=context)
