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

from openerp.osv import orm
from openerp.addons.base_iban.base_iban import _ref_iban, _format_iban, _pretty_iban
import logging
_logger = logging.getLogger(__name__)


def check_iban(iban):
    """
    Check the IBAN number (logic partially based upon base_iban module, cf. is_iban_valid method)
    """
    iban = _format_iban(iban).lower()
    if iban[:2] not in _ref_iban:
        return False
    if len(iban) != len(_format_iban(_ref_iban[iban[:2]])):
        return False
    #the four first digits have to be shifted to the end
    iban = iban[4:] + iban[:4]
    #letters have to be transformed into numbers (a = 10, b = 11, ...)
    iban2 = ""
    for char in iban:
        if char.isalpha():
            iban2 += str(ord(char)-87)
        else:
            iban2 += char
    #iban is correct if modulo 97 == 1
    return int(iban2) % 97 == 1


class res_partner_bank(orm.Model):
    _inherit = 'res.partner.bank'

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name:
            ids = self.search(cr, user, [('acc_number', operator, name)] + args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        '''
        format iban in case of exact search
        
        Suggestion for OpenERP:
        The code below could be simplified if account numbers were stored in the database in 'normalised' format
        i.e. without spaces or other formatting characters (such as '-').
        '''
        #_logger.warn('%s, search, args=%s', self._name, args)
        i = 0
        new_args = []
        for arg in args:
            if arg[0] == 'acc_number' and arg[2]:
                acc_number = arg[2].replace(' ','').replace('-', '').upper()
                if arg[1] in ['=', '=like', '=ilike']:
                    cr.execute("SELECT id FROM "
                        "(SELECT id, state, acc_number, %s AS len_acc_number FROM res_partner_bank) b "
                        "WHERE "
                        # Belgium: BBAN is always 12 chars and subset of IBAN
                        "  state='iban' AND UPPER(SUBSTRING(acc_number FOR 2)) = 'BE' AND len_acc_number = 12 "
                        "    AND UPPER(REPLACE(REPLACE(acc_number, ' ', ''), '-','')) LIKE '%%'|| %s ||'%%'"
                        # other countries
                        "  OR UPPER(REPLACE(REPLACE(acc_number, ' ', ''), '-','')) = %s"
                        , 
                        (len(acc_number), acc_number, acc_number))
                    res = cr.fetchall()
                    if res:
                        rpb_ids = map(lambda x: x[0], res)
                        new_args.append(['id', 'in', rpb_ids])
                else:
                    new_args.extend(['|', arg, [arg[0], arg[1], acc_number]])
            else:
                new_args.append(arg)
            i += 1
        #_logger.warn('%s, search, new_args=%s', self._name, new_args)
        return super(res_partner_bank,self).search(cr, uid, new_args, offset, limit, order, context=context, count=count)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
