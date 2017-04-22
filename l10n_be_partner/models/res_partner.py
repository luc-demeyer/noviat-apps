# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registry_authority = fields.Selection(
        selection='_selection_registry_authority', string='Registry Authority')
    registry_number = fields.Char(
        string='Registered Company Number',
        help="Use this field to register the unique number attributed "
             "by the authorities to the legal entity of this partner."
             "\ne.g KBO/BCE number for Belgium.")

    @api.model
    def _selection_registry_authority(self):
        return [('kbo_bce', 'Belgium - KBO/BCE')]

    @api.one
    @api.constrains('registry_number')
    def _check_registry_number(self):
        success = True
        if self.is_company and self.registry_authority == 'kbo_bce':
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

    @api.model
    def create(self, vals):
        self._handle_registry_number(vals)
        partner = super(ResPartner, self).create(vals)
        if not self._context.get('skip_kbo_bce') and vals.get('is_company'):
            if vals.get('vat') or vals.get('registry_number'):
                partner._handle_kbo_bce()
        return partner

    @api.multi
    def write(self, vals):
        self._handle_registry_number(vals)
        # update context to avoid useless _field_sync processing
        ctx = dict(self._context, skip_kbo_bce=True)
        partners = self.with_context(ctx)
        super(ResPartner, partners).write(vals)
        if not self._context.get('skip_kbo_bce'):
            if vals.get('vat') or vals.get('registry_number'):
                partners._handle_kbo_bce()
        return True

    def _handle_registry_number(self, vals):
        rn = vals.get('registry_number')
        if vals.get('registry_authority') == 'kbo_bce' and rn:
            vals['registry_number'] = self._format_registry_number(rn)

    def _format_registry_number(self, number):
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

    def _handle_kbo_bce(self):

        be = self._get_belgium()

        for partner in self:
            if not partner.is_company:
                continue
            vals = {}
            kbo_number = False
            # handle companies without VAT obligation
            vat = partner.vat
            rn = partner.registry_number
            ra = partner.registry_authority

            if vat and vat[0:2].upper() == 'BE' and not rn and not ra:
                kbo_number = True
                rn = vat[2:]
                vals['registry_number'] = self._format_registry_number(rn)
                vals['registry_authority'] = 'kbo_bce'

            if ra == 'kbo_bce' and rn and not vat:
                kbo_number = True
                vat_number = rn.replace('.', '')
                if self.vies_vat_check('BE', vat_number):
                    vals.update({
                        'vat': 'BE ' + vat_number,
                        'vat_subjected': True,
                    })

            if kbo_number and not partner.country_id:
                vals['country_id'] = be.id

            partner._handle_kbo_bce_write(vals)

    def _handle_kbo_bce_write(self, vals):
        """
        Use this method for extra customisations, e.g.
        lookup in external databases.
        """
        super(ResPartner, self).write(vals)
