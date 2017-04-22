# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    rml_header1 = fields.Char(translate=True)
    rml_footer = fields.Text(translate=True)
    company_registry = fields.Char(
        help="Company Registry, e.g. RPR Gent, RPM Namur.")

    @api.one
    @api.constrains('company_registry')
    def _check_company_registry(self):
        """
        Company registry is a required field on Belgian invoices
        """
        if self.country_id.code == 'BE' and not self.company_registry:
            raise ValidationError(
                _("Please complete the 'Company Registry' field !"))
