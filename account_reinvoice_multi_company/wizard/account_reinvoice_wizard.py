# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import models

_logger = logging.getLogger(__name__)


class AccountReinvoiceWizard(models.TransientModel):
    _inherit = 'account.reinvoice.wizard'

    def _prepare_out_invoice_vals(self, partner, journal):
        inv_vals = super(AccountReinvoiceWizard, self).\
            _prepare_out_invoice_vals(partner, journal)
        inv_vals['intercompany_invoice'] = partner.intercompany_invoice
        return inv_vals
