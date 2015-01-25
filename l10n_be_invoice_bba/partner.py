# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011-now Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields, api


class res_partner(models.Model):
    """
    add field to indicate default 'Communication Type' on customer invoices
    """
    _inherit = 'res.partner'

    @api.model
    def _get_comm_type(self):
        res = self.env['account.invoice']._get_reference_type()
        return res

    out_inv_comm_type = fields.Selection(
        '_get_comm_type', string='Communication Type',
        change_default=True, default='none',
        help='Select Default Communication Type for Outgoing Invoices.')
    out_inv_comm_algorithm = fields.Selection(
        [('random', 'Random'),
         ('date', 'Date'),
         ('partner_ref', 'Customer Reference'),
         ], string='Communication Algorithm',
        help="Select Algorithm to generate the "
             "Structured Communication on Outgoing Invoices.")

    @api.model
    def _commercial_fields(self):
        return super(res_partner, self)._commercial_fields() + \
            ['out_inv_comm_type', 'out_inv_comm_algorithm']
