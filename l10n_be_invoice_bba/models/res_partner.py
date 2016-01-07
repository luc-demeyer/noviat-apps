# -*- encoding: utf-8 -*-
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

from openerp import models, fields, api


class ResPartner(models.Model):
    """
    add field to indicate default 'Communication Type' on customer invoices
    """
    _inherit = 'res.partner'

    out_inv_comm_type = fields.Selection(
        '_get_comm_type', string='Communication Type',
        change_default=True, default='none',
        help='Select Default Communication Type for Outgoing Invoices.')
    out_inv_comm_algorithm = fields.Selection(
        '_get_out_inv_comm_algorithm', string='Communication Algorithm',
        help="Select Algorithm to generate the "
             "Structured Communication on Outgoing Invoices.")

    @api.model
    def _get_comm_type(self):
        res = self.env['account.invoice']._get_reference_type()
        return res

    @api.model
    def _get_out_inv_comm_algorithm(self):
        return [('random', 'Random'),
                ('date', 'Date'),
                ('partner_ref', 'Customer Reference')]

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + \
            ['out_inv_comm_type', 'out_inv_comm_algorithm']

    @api.onchange('supplier')
    def _onchange_supplier(self):
        """ don't set 'bba' for suppliers """
        if self.supplier and not self.customer:
            if self.out_inv_comm_type == 'bba':
                self.out_inv_comm_type = 'none'
