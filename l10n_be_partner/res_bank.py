# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class res_partner_bank(models.Model):
    _inherit = 'res.partner.bank'

    def create(self, cr, uid, vals, context=None):
        if vals.get('state') != 'iban':
            env = api.Environment(cr, uid, context)
            bank = env['res.bank'].browse(vals.get('bank'))
            if bank.country == env.ref('base.be') and bank.bic and bank.code:
                vals['state'] = 'iban'
                vals['acc_number'] = \
                    env['res.bank'].bban2iban('be', vals['acc_number'])
        return super(res_partner_bank, self).create(cr, uid, vals, context)


class res_bank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char(
        string='Code',
        help="Country specific Bank Code")

    @api.model
    def bban2iban(self, country_code, bban):
        # TODO: extend to other countries
        if country_code not in ['be']:
            raise Warning(
                _("'%s': bban conversion not supported for country '%s' !")
                % (bban, country_code))
        success = True
        nr = bban.replace('-', '').replace(' ', '')
        try:
            int(nr)
        except:
            success = False
        if len(nr) != 12:
            success = False
        if not success:
            raise Warning(_("'%s': Incorrect BBAN Number !") % bban)
        kk = calc_iban_checksum('BE', nr)
        return 'BE' + kk + nr


def calc_iban_checksum(country, bban):
    bban += country + '00'
    base = ''
    for c in bban:
        if c.isdigit():
            base += c
        else:
            base += str(ord(c) - ord('A') + 10)
    kk = 98 - int(base) % 97
    return str(kk).rjust(2, '0')
