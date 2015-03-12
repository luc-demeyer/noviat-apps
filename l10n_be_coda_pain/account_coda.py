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

from openerp.osv import orm, fields


class coda_bank_account(orm.Model):
    _inherit= 'coda.bank.account'

    _columns = {
        'find_payment': fields.boolean('Lookup Payment Reference', 
            help="Invoice lookup and reconciliation via the SEPA EndToEndReference."
                 "\nInstall the 'account_pain' module if you want to take advantage of this feature."),
    }
    _defaults = {
        'find_payment': True,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
