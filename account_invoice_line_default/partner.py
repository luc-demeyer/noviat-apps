# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'property_in_inv_acc': fields.property(
            type='many2one',
            relation='account.account',
            string='Incoming Invoice Account',
            domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
            help="Default Account on incoming Invoices."),
        'property_out_inv_acc': fields.property(
            type='many2one',
            relation='account.account',
            string='Outgoing Invoice Account',
            domain=[('type', '<>', 'view'), ('type', '<>', 'closed')],
            help="Default Account on outgoing Invoices."),
    }
