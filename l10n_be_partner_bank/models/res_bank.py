# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResBank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char(
        string='Code',
        help="Country specific Bank Code")

    @api.model
    def bban2iban(self, country_code, bban):
        # TODO: extend to other countries
        if country_code not in ['be']:
            raise UserError(
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
