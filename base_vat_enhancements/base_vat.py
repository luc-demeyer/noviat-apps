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

from openerp import models, api, _
from openerp.exceptions import Warning
from openerp.addons.base_vat.base_vat import _ref_vat
import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
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

    def _check_vat(self, vat):
        if not vat:
            return True
        online = False
        if not self._context.get('simple_vat_check'):
            online = self.env.user.company_id.vat_check_vies
        if online:
            check_func = self.pool['res.partner'].vies_vat_check
        else:
            check_func = self.pool['res.partner'].simple_vat_check
        vat_country, vat_number = self._split_vat(vat)
        return check_func(self._cr, self._uid,
                          vat_country, vat_number, context=self._context)

    def _vat_check_errmsg(self, vat, partner_name):
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        msg = _("VAT number validation for partner '%s' "
                "with VAT number '%s' failed.") % (partner_name, vat)
        msg += '\n'
        vat_country, vat_number = self._split_vat(vat)
        if vat_country.isalpha():
            vat_no = _ref_vat[vat_country] \
                if vat_country in _ref_vat else vat_no
            check_vies = self.env.user.company_id.vat_check_vies
            if check_vies:
                msg += _("The VAT number either failed the "
                         "VIES VAT validation check or did "
                         "not respect the expected format %s.") % vat_no
                return msg
        msg += _("This VAT number does not seem to be "
                 "valid.\nNote: the expected format is %s") % vat_no
        return msg

    @api.model
    def create(self, vals):
        """ add vat check to create """
        if vals.get('vat'):
            if not self._check_vat(vals['vat']):
                msg = self._vat_check_errmsg(
                    vals['vat'], vals.get('name', ''))
                raise Warning(msg)
            vals['vat'] = vals['vat'].replace(' ', '').upper()
        return super(res_partner, self).create(vals)

    @api.multi
    def write(self, vals):
        """ add vat check to write """
        for partner in self:
            if vals.get('vat'):
                if not self.with_context(
                        {'simple_vat_check': True})._check_vat(vals['vat']):
                    partner_name = vals.get('name') or partner.name
                    msg = self._vat_check_errmsg(vals['vat'], partner_name)
                    raise Warning(msg)
                vals['vat'] = vals['vat'].replace(' ', '').upper()
        return super(res_partner, self).write(vals)

    @api.multi
    def button_check_vat(self):
        self.ensure_one()
        if not self.check_vat():
            msg = self._vat_check_errmsg(
                self.vat, self.name or "")
            raise Warning(msg)
        else:
            raise Warning(_('VAT Number Check OK'))

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
