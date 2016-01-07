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

import re
import time
import random
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    reference = fields.Char(string='Communication')
    reference_type = fields.Selection(string='Communication Type')

    @api.model
    def _get_reference_type(self):
        """
        Add BBA Structured Communication Type and change labels
        from 'reference' into 'communication'
        """
        res = super(AccountInvoice, self)._get_reference_type()
        res[[i for i, x in enumerate(res) if x[0] == 'none'][0]] = \
            ('none', _('Free Communication'))
        res.append(('bba', _('BBA Structured Communication')))
        return res

    def check_bbacomm(self, val):
        supported_chars = '0-9+*/ '
        pattern = re.compile('[^' + supported_chars + ']')
        if pattern.findall(val or ''):
            return False
        bbacomm = re.sub('\D', '', val or '')
        if len(bbacomm) == 12:
            base = int(bbacomm[:10])
            mod = base % 97 or 97
            if mod == int(bbacomm[-2:]):
                return True
        return False

    def duplicate_bba(self, partner, reference):
        """
        overwrite this method to customize the handling of
        duplicate BBA communications
        """
        if partner.out_inv_comm_algorithm == 'random':
            # generate new bbacom to cope with duplicate bba coming
            # out of random generator
            reference = self.generate_bbacomm(partner)
        else:
            # replace duplicate BBA Comms created manually
            # or by Odoo applications (eg Sales Order Refund/Modify)
            reference = self.generate_bbacomm(partner)

        dups = self.search(
            [('type', '=', 'out_invoice'),
             ('state', '!=', 'draft'),
             ('reference_type', '=', 'bba'),
             ('reference', '=', reference)])
        if dups:
            raise Warning(
                _("The BBA Structured Communication "
                  "has already been used!"
                  "\nPlease use a unique BBA Structured Communication."))
        return reference

    @api.one
    @api.constrains('reference_type', 'reference')
    def _check_communication(self):
        if self.reference_type == 'bba' and \
                not self.check_bbacomm(self.reference):
            raise Warning(_('Invalid BBA Structured Communication !'))

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False):
        result = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice, payment_term, partner_bank_id,
            company_id)
        reference = False
        reference_type = 'none'
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            partner = partner.commercial_partner_id
            if type == 'out_invoice':
                reference_type = partner.out_inv_comm_type or 'none'
                if reference_type == 'bba':
                    reference = self.generate_bbacomm(partner)
        res_update = {
            'reference_type': reference_type,
            'reference': reference,
        }
        result['value'].update(res_update)
        return result

    @api.onchange('reference_type')
    def _onchange_reference_type(self):
        if self.reference_type == 'bba' and self.type == 'out_invoice':
            partner = self.partner_id.commercial_partner_id
            self.reference = self.generate_bbacomm(partner)

    def format_bbacomm(self, val):
        bba = re.sub('\D', '', val)
        bba = '+++%s/%s/%s+++' % (
            bba[0:3], bba[3:7], bba[7:])
        return bba

    def _generate_bbacomm_hook(self, partner, algorithm):
        """
        hook to add customer specific algorithm
        """
        raise Warning(
            _("Unsupported Structured Communication Type "
              "Algorithm '%s' !"
              "\nPlease contact your Odoo support channel.")
            % algorithm)

    def generate_bbacomm(self, partner):
        algorithm = 'random'
        if partner:
            algorithm = partner.out_inv_comm_algorithm or 'random'
        else:
            partner = False

        if algorithm == 'date':
            doy = time.strftime('%j')
            year = time.strftime('%Y')
            seq = '001'
            sequences = self.search(
                [('type', '=', 'out_invoice'),
                 ('reference_type', '=', 'bba'),
                 ('reference', 'like', '+++%s/%s/%%' % (doy, year))],
                order='reference')
            if sequences:
                prev_seq = int(sequences[-1].reference[12:15])
                if prev_seq < 999:
                    seq = '%03d' % (prev_seq + 1)
                else:
                    raise Warning(
                        _("The daily maximum of outgoing invoices "
                          "with an automatically generated "
                          "BBA Structured Communication "
                          "has been exceeded!"
                          "\nPlease create manually a unique "
                          "BBA Structured Communication."))
            bbacomm = doy + year + seq
            base = int(bbacomm)
            mod = base % 97 or 97
            reference = '+++%s/%s/%s%02d+++' % (doy, year, seq, mod)

        elif algorithm == 'partner_ref':
            partner_ref = partner and partner.ref
            partner_ref_nr = re.sub('\D', '', partner_ref or '')
            if (len(partner_ref_nr) < 3) or \
                    (len(partner_ref_nr) > 7):
                raise Warning(
                    _("The Partner should have a 3-7 digit "
                      "Reference Number for the generation of "
                      "BBA Structured Communications!' \
                      '\nPlease correct the Partner record."))
            else:
                partner_ref_nr = partner_ref_nr.ljust(7, '0')
                seq = '001'
                sequences = self.search(
                    [('type', '=', 'out_invoice'),
                     ('reference_type', '=', 'bba'),
                     ('reference', 'like', '+++%s/%s/%%' % (
                         partner_ref_nr[:3], partner_ref_nr[3:]))
                     ], order='reference')
                if sequences:
                    prev_seq = int(sequences[-1].reference[12:15])
                    if prev_seq < 999:
                        seq = '%03d' % (prev_seq + 1)
                    else:
                        raise Warning(
                            _("The daily maximum of outgoing "
                              "invoices with an automatically "
                              "generated BBA Structured "
                              "Communications has been exceeded!"
                              "\nPlease create manually a unique"
                              "BBA Structured Communication."))
            bbacomm = partner_ref_nr + seq
            base = int(bbacomm)
            mod = base % 97 or 97
            reference = '+++%s/%s/%s%02d+++' % (
                partner_ref_nr[:3], partner_ref_nr[3:], seq, mod)

        elif algorithm == 'random':
            base = random.randint(1, 9999999999)
            bbacomm = str(base).rjust(10, '0')
            base = int(bbacomm)
            mod = base % 97 or 97
            mod = str(mod).rjust(2, '0')
            reference = '+++%s/%s/%s%s+++' % (
                bbacomm[:3], bbacomm[3:7], bbacomm[7:], mod)

        else:
            reference = self._generate_bbacomm_hook(
                partner, algorithm)

        return reference

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date, period_id, description, journal_id)
        res['reference_type'] = self.reference_type
        return res

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        partner_id = vals.get('partner_id')
        if not partner_id:
            raise Warning(
                _('Please fill in the Partner field.'))
        partner = self.env['res.partner'].browse(partner_id)
        partner = partner.commercial_partner_id
        if vals.get('type'):
            inv_type = vals.get('type')
        else:
            inv_type = self._context.get('type', 'out_invoice')
            vals['type'] = inv_type
        reference_type = vals.get('reference_type')
        if not reference_type and inv_type == 'out_invoice':
            reference_type = partner.out_inv_comm_type
        reference = vals.get('reference')

        if reference_type == 'bba':
            if inv_type == 'out_invoice':
                if not self.check_bbacomm(reference):
                    reference = self.generate_bbacomm(partner)
                    dups = self.search(
                        [('type', '=', 'out_invoice'),
                         ('state', '!=', 'draft'),
                         ('reference_type', '=', 'bba'),
                         ('reference', '=', reference)])
                    if dups:
                        reference = self.duplicate_bba(partner, reference)
            else:
                if not reference:
                    raise Warning(
                        _("Empty BBA Structured Communication!"
                          "\nPlease fill in a "
                          "BBA Structured Communication."))
                elif self.check_bbacomm(reference):
                    reference = self.format_bbacomm(reference)
            vals.update({
                'reference_type': reference_type,
                'reference': reference})
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def write(self, vals):
        for inv in self:
            if inv.state == 'draft':
                if 'reference_type' in vals:
                    reference_type = vals['reference_type']
                else:
                    reference_type = inv.reference_type
                if reference_type == 'bba':
                    if 'reference' in vals:
                        bbacomm = vals['reference']
                    else:
                        bbacomm = inv.reference or ''
                    if self.check_bbacomm(bbacomm):
                        reference = self.format_bbacomm(bbacomm)
                        if inv.type == 'out_invoice':
                            dups = self.search(
                                [('id', '!=', inv.id),
                                 ('type', '=', 'out_invoice'),
                                 ('state', '!=', 'draft'),
                                 ('reference_type', '=', 'bba'),
                                 ('reference', '=', reference)])
                            if dups:
                                partner = inv.partner_id.commercial_partner_id
                                reference = self.duplicate_bba(
                                    partner, reference)
                        if reference != inv.reference:
                            vals['reference'] = reference
            super(AccountInvoice, self).write(vals)
        return True

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        if self.type == 'out_invoice':
            reference_type = self.reference_type
            default['reference_type'] = reference_type
            if reference_type == 'bba':
                partner = self.partner_id.commercial_partner_id
                default['reference'] = self.generate_bbacomm(partner)
        return super(AccountInvoice, self).copy(default)
