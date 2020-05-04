# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    """
    FODFIN Notice 725:
    All customers with Belgian VAT number must be included in the annual
    VAT Listing, except those with only operations according article 44
    of the VAT lawbook (reported via tax code 00).
    You should uncheck the 'vat_subjected' flag for those customers.
    """
    _inherit = 'res.partner'

    vat_subjected = fields.Boolean(
        string='VAT Subjected',
        default=lambda self: self._default_vat_subjected(),
        help="Uncheck this flag to exclude this partner from certain "
             "VAT declarations (e.g. the Belgian Annual Listing of "
             "VAT subjected Customers).")

    @api.model
    def _default_vat_subjected(self):
        if self.company_type == 'company':
            return self.vat and True or False

    @api.onchange('vat')
    def _onchange_vat(self):
        self.vat_subjected = self.vat and True or False
        if hasattr(super(ResPartner, self), '_onchange_vat'):
            super(ResPartner, self)._onchange_vat()
