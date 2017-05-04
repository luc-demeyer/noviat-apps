# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        company = super(ResCompany, self).create(vals)
        company.partner_id.company_partner_flag = True
        return company
