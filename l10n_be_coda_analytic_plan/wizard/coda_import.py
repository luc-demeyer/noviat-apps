# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class AccountCodaImport(models.TransientModel):
    _inherit = 'account.coda.import'

    def _prepare_mv_line_dict(self, st_line, cba, transaction):
        mv_line_dict = super(AccountCodaImport, self)._prepare_mv_line_dict(
            st_line, cba, transaction)
        if transaction.get('analytics_id'):
            mv_line_dict['analytics_id'] = transaction['analytics_id']
        return mv_line_dict
