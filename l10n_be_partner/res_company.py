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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class res_company(models.Model):
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
