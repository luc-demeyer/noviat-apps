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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    """
    TODO:
    move registry_authority & registry_number fields to separate
    module for use by localization modules of other countries
    """
    _inherit = 'res.partner'

    def _format_registry_number(self, number):
        res = number.replace(' ', '').replace('.', '')
        res = res[:4] + '.' + res[4:7] + '.' + res[7:]
        return res

    @api.one
    @api.constrains('registry_number')
    def _check_registry_number(self):
        success = True
        if self.is_company:
            if self.vat and self.vat[0:2].upper() == 'BE':
                rn = self.registry_number.replace(' ', '').replace('.', '')
                rn_check = self.vat[2:].replace(' ', '').replace('.', '')
                if rn != rn_check:
                    success = False
            else:
                if self.country_id and self.country_id.code == 'BE':
                    rn = self.registry_number and \
                        self.registry_number.replace(' ', '').replace('.', '')
                    if rn:
                        if len(rn) != 10:
                            success = False
                        try:
                            int(rn)
                        except:
                            success = False
        if not success:
            raise ValidationError(_("Incorrect Registry Number !"))

    registry_number = fields.Char(
        string='Registered Company Number',
        help="Use this field to register the unique number attributed "
             "by the authorities to the legal entity of this partner."
             "\ne.g KBO/BCE number for Belgium.")

    @api.model
    def _get_registry_authority(self):
        return [('kbo_bce', 'Belgium - KBO/BCE')]

    registry_authority = fields.Selection(
        _get_registry_authority, string='Registry Authority')

    def _commercial_fields(self, cr, uid, context=None):
        res = super(res_partner, self)._commercial_fields(
            cr, uid, context=context)
        return res + ['registry_number', 'registry_authority']

    def create(self, cr, uid, vals, context=None):
        if vals.get('is_company'):
            be_id = self.pool['res.country'].search(
                cr, uid, [('code', '=', 'BE')])[0]
            # handle vat number
            if vals.get('vat'):
                vat = vals.get('vat')
                if vat[0:2].upper() == 'BE':
                    # set KBO Number
                    rn = vat[2:]
                    if not vals.get('registry_number'):
                        vals['registry_number'] = \
                            self._format_registry_number(rn)
                        vals['registry_authority'] = 'kbo_bce'
                    # update vat_subjected flag
                    if not vals.get('vat_subjected'):
                        vals['vat_subjected'] = True
                    # set country
                    if vals.get('country_id') != be_id:
                        vals['country_id'] = be_id
            elif vals.get('registry_authority'):
                if vals['registry_authority'] == 'kbo_bce':
                    if vals.get('country_id') != be_id:
                        vals['country_id'] = be_id
        return super(res_partner, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        # _logger.warn('%s, write, vals=%s', self._name, vals)
        if isinstance(ids, (int, long)):
            ids = [ids]
        for partner in self.browse(cr, uid, ids, context):
            if not partner.is_company:
                continue
            vat = vals.get('vat') or partner.vat
            rn = vals.get('registry_number') or partner.registry_number
            country_id = vals.get('country_id') or partner.country_id.id
            be_id = self.pool['res.country'].search(
                cr, uid, [('code', '=', 'BE')])[0]
            kbo_number = False

            # handle registry_number
            if rn and (
                    vat and vat[0:2].upper() == 'BE' or country_id == be_id):
                kbo_number = True
                vals['registry_number'] = self._format_registry_number(rn)
                vals['registry_authority'] = 'kbo_bce'
                if not vat:
                    vat_number = vals['registry_number'].replace('.', '')
                    if self.vies_vat_check(cr, uid, 'BE', vat_number,
                                           context=context):
                        vals.update({
                            'vat': 'BE ' + vat_number,
                            'vat_subjected': True,
                        })

            # handle vat number
            if vat and vat[0:2].upper() == 'BE':
                # set KBO Number
                kbo_number = True
                rn = vat[2:]
                vals['registry_authority'] = 'kbo_bce'
                vals['registry_number'] = self._format_registry_number(rn)
                # update vat_subjected flaf
                if not ('vat_subjected' in vals or partner.vat_subjected):
                    vals['vat_subjected'] = True

            if kbo_number and country_id != be_id:
                vals['country_id'] = be_id

        return super(res_partner, self).write(cr, uid, ids, vals, context)
