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
from openerp.tools.translate import _
from openerp.addons.base_vat.base_vat import _ref_vat
import string
import logging
_logger = logging.getLogger(__name__)


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def _auto_init(self, cr, context=None):
        """ normalise all vat fields in the database """
        cr.execute("UPDATE res_partner SET vat=upper(replace(vat, ' ', ''))")
        return super(res_partner, self)._auto_init(cr, context=context)

    def __init__(self, pool, cr):
        """ remove check_vat constraint """
        super(res_partner, self).__init__(pool, cr)
        for i, tup in enumerate(self._constraints):
            if hasattr(tup[0], '__name__') and tup[0].__name__ == 'check_vat':
                del self._constraints[i]

    def _check_vat(self, cr, uid, vat, context=None):
        user_company = self.pool.get('res.users').browse(
            cr, uid, uid).company_id
        if user_company.vat_check_vies:
            check_func = self.vies_vat_check
        else:
            check_func = self.simple_vat_check
        if not vat:
            return True
        vat_country, vat_number = self._split_vat(vat)
        return check_func(cr, uid, vat_country, vat_number, context=context)

    def create(self, cr, uid, vals, context=None):
        """ add vat check to create """
        if vals.get('vat'):
            if not self._check_vat(cr, uid, vals['vat'], context):
                msg = _("VAT number validation for partner '%s' "
                        "with VAT number '%s' failed.") \
                    % (vals.get('name', ''), vals['vat'])

                def default_vat_check(cn, vn):
                    # by default, a VAT number is valid if:
                    #  it starts with 2 letters
                    #  has more than 3 characters
                    return cn[0] in string.ascii_lowercase and \
                        cn[1] in string.ascii_lowercase

                vat_country, vat_number = self._split_vat(vals['vat'])
                vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
                if default_vat_check(vat_country, vat_number):
                    vat_no = _ref_vat[vat_country] if \
                        vat_country in _ref_vat else vat_no
                msg += '\n' + _("This VAT number does not seem to be valid."
                                "\nNote: the expected format is %s") % vat_no
                raise orm.except_orm(_('Error'), msg)
            vals['vat'] = vals['vat'].replace(' ', '').upper()
        return super(res_partner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """ add vat check to write """
        if isinstance(ids, (int, long)):
            ids = [ids]
        if ids and vals.get('vat'):
            if not self._check_vat(cr, uid, vals['vat'], context):
                partner = self.browse(cr, uid, ids[0], context=context)
                msg = _("VAT number validation for partner '%s' "
                        "with VAT number '%s' failed.") \
                    % (vals.get('name', partner.name), vals['vat'])
                msg += self._construct_constraint_msg(
                    cr, uid, [partner.id], context=context)
                raise orm.except_orm(_('Error'), msg)
            vals['vat'] = vals['vat'].replace(' ', '').upper()
        return super(res_partner, self).write(
            cr, uid, ids, vals, context=context)

    def button_check_vat(self, cr, uid, ids, context=None):
        if not self.check_vat(cr, uid, ids, context=context):
            msg = self._construct_constraint_msg(
                cr, uid, ids, context=context)
            raise orm.except_orm(_('Error'), msg)
        else:
            raise orm.except_orm(
                _('Check OK'),
                _('VAT Number Check OK'))

    def search(self, cr, uid, args, offset=0,
               limit=None, order=None, context=None, count=False):
        """
        normalise vat argument before search
        """
        for arg in args:
            if arg[0] == 'vat' and arg[2]:
                arg = (arg[0], arg[1], arg[2].replace(' ', '').upper())
        return super(res_partner, self).search(
            cr, uid, args, offset, limit, order, context=context, count=count)
