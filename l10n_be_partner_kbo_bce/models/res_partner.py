# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    kbo_bce_number = fields.Char(
        string='KBO/BCE Number',
        compute=lambda s: s._compute_identification(
            'kbo_bce_number', 'l10n_be_kbo_bce',
        ),
        inverse=lambda s: s._inverse_identification(
            'kbo_bce_number', 'l10n_be_kbo_bce',
        ),
        search=lambda s, *a: s._search_identification(
            'l10n_be_kbo_bce', *a
        ),
    )
    country_code = fields.Char(
        related='country_id.code', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('is_company'):
            if 'vat' in vals or 'kbo_bce_number' in vals:
                self._sync_kbo_bce_number(vals)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        # base module, res_partner.py drops 'is_company' from vals
        # hence we save vals before super()
        vals_in = vals.copy()
        if 'is_company' in vals_in:
            if vals_in['is_company']:
                company_partners = self
            else:
                company_partners = self.env['res.partner']
        else:
            company_partners = self.filtered(lambda r: r.is_company)
        contact_partners = self - company_partners

        super(ResPartner, contact_partners).write(vals)
        for partner in company_partners:
            values = vals_in.copy()
            if any([x in vals_in for x in ['vat', 'kbo_bce_number',
                                           'is_company', 'country_id']]):
                if 'vat' in vals_in:
                    vat = vals_in['vat']
                else:
                    vat = partner.vat
                if 'kbo_bce_number' in vals_in:
                    kbo_bce_number = vals_in['kbo_bce_number']
                else:
                    kbo_bce_number = partner.kbo_bce_number
                if 'country_id' in vals_in:
                    country_id = vals_in['country_id']
                else:
                    country_id = partner.country_id.id
                sync_vals = {
                    'vat': vat,
                    'kbo_bce_number': kbo_bce_number,
                    'country_id': country_id,
                }
                partner._sync_kbo_bce_number(sync_vals)
                for k in sync_vals:
                    values[k] = sync_vals[k]
            super(ResPartner, partner).write(values)
        return True

    def _vals_format_kbo_bce_number(self, vals):
        rn = vals.get('kbo_bce_number')
        if rn:
            vals['kbo_bce_number'] = self._format_kbo_bce_number(rn)

    def _format_kbo_bce_number(self, number):
        res = number.replace(' ', '').replace('.', '')
        res = res[:4] + '.' + res[4:7] + '.' + res[7:]
        return res

    def _get_belgium(self):
        be = self.env.ref('base.be') or self.env['res.country'].search(
            [('code', '=', 'BE')])
        if not be:
            raise ValidationError(_(
                "Configuration Error, Country BE has not been defined !"))
        return be

    def _sync_kbo_bce_number(self, sync_vals):
        be = self._get_belgium()
        vat = sync_vals.get('vat') and self._sanitize_vat(sync_vals['vat'])
        kbn = sync_vals.get('kbo_bce_number') and sync_vals['kbo_bce_number']
        country_id = sync_vals.get('country_id') and sync_vals['country_id']
        has_kbo_bce_number = False

        if vat and vat[0:2] == 'BE' and not kbn:
            kbn = vat[2:]
            sync_vals['kbo_bce_number'] = kbn
            has_kbo_bce_number = True

        if kbn and not vat:
            has_kbo_bce_number = True
            vat_number = kbn.replace('.', '')
            if self.vies_vat_check('BE', vat_number):
                sync_vals['vat'] = 'BE ' + vat_number
                # cf. l10n_be_coa_multilang for the 'vat_subjected' field
                if hasattr(self, 'vat_subjected'):
                    sync_vals['vat_subjected'] = True

        if has_kbo_bce_number and not country_id:
            sync_vals['country_id'] = be.id

        self._vals_format_kbo_bce_number(sync_vals)
        self._update_kbo_bce_sync_vals(sync_vals)

        # consistency check
        kbn = sync_vals.get('kbo_bce_number')
        vat = sync_vals.get('vat')
        if kbn and vat:
            if kbn.replace('.', '') != self._sanitize_vat(vat)[2:]:
                raise ValidationError(_(
                    "KBO/BCE Number '%s' is not consistent with "
                    "VAT Number '%s'.") % (kbn, vat)
                )

        # minimise overhead caused by sync of _commercial_fields
        # and address fields to child records
        if self.vat == sync_vals.get('vat'):
            del sync_vals['vat']
        if self.country_id.id == sync_vals.get('country_id'):
            del sync_vals['country_id']

    def _update_kbo_bce_sync_vals(self, sync_vals):
        """
        Use this method for extra customisations, e.g.
        lookup in external databases.

        in case of 'create': empty self, sync_vals contains all vals
        in case of 'write': self contains partner record
        """
        pass
