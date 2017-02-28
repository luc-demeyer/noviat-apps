# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _prepare_mv_line_dict(self, st_line, cba, transaction):
        mv_line_dict = super(AccountCodaImport, self)._prepare_mv_line_dict(
            st_line, cba, transaction)
        for f in ['product_id', 'reinvoice_key_id']:
            if transaction.get(f):
                mv_line_dict[f] = transaction[f]
        return mv_line_dict
