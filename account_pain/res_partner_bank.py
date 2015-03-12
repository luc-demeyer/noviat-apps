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

from openerp.osv import fields, orm
import logging
_logger = logging.getLogger(__name__)


class res_partner_bank(orm.Model):
    _inherit = "res.partner.bank"

    _columns = {
        'charge_bearer': fields.selection([
            ('CRED','Borne By Creditor'),
            ('DEBT','Borne By Debtor'),
            ('SHAR', 'Shared'),
            ('SLEV', 'Following Service Level'),
            ], 'Charge Bearer',
            help="Specifies which party/parties will bear the charges linked to the processing of the payment transaction.")
    }
    _defaults = {
        'charge_bearer': 'SLEV',
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
