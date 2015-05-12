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

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.base_vat.base_vat import _ref_vat
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

    def _vat_check_errmsg(self, cr, uid, vat, partner_name, context=None):
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        msg = _("VAT number validation for partner '%s' "
                "with VAT number '%s' failed.") % (partner_name, vat)
        msg += '\n'
        vat_country, vat_number = self._split_vat(vat)
        if vat_country.isalpha():
            vat_no = _ref_vat[vat_country] \
                if vat_country in _ref_vat else vat_no
            check_vies = self.pool['res.users'].browse(
                cr, uid, uid).company_id.vat_check_vies
            if check_vies:
                msg += _("The VAT number either failed the "
                         "VIES VAT validation check or did "
                         "not respect the expected format %s.") % vat_no
                return msg
        msg += _("This VAT number does not seem to be "
                 "valid.\nNote: the expected format is %s") % vat_no
        return msg

    def create(self, cr, uid, vals, context=None):
        """ add vat check to create """
        if vals.get('vat'):
            if not self._check_vat(cr, uid, vals['vat'], context):
                msg = self._vat_check_errmsg(
                    cr, uid, vals['vat'], vals.get('name', ''),
                    context=context)
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
                partner_name = vals.get('name') or partner.name
                msg = self._vat_check_errmsg(
                    cr, uid, vals['vat'], partner_name, context=context)
                raise orm.except_orm(_('Error'), msg)
            vals['vat'] = vals['vat'].replace(' ', '').upper()
        return super(res_partner, self).write(
            cr, uid, ids, vals, context=context)

    def button_check_vat(self, cr, uid, ids, context=None):
        if not self.check_vat(cr, uid, ids, context=context):
            partner = self.browse(cr, uid, ids[0], context=context)
            msg = self._vat_check_errmsg(
                cr, uid, partner.vat, partner.name or "", context=context)
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
        for i, arg in enumerate(args):
            if arg[0] == 'vat' and arg[2]:
                args[i] = (arg[0], arg[1], arg[2].replace(' ', '').upper())
        return super(res_partner, self).search(
            cr, uid, args, offset, limit, order, context=context, count=count)
