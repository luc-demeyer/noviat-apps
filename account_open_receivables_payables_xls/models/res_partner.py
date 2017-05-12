# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
# from openerp.addons.report_xls.utils import _render


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _xls_query_extra(self):
        """
        allow inherited modules to extend the query
        """
        select_extra = ""
        join_extra = ""
        where_extra = ""
        return select_extra, join_extra, where_extra

    @api.model
    def _xls_arap_overview_fields(self):
        """
        change list in custom module to add/drop columns or change order
        of the partner summary table
        """
        return [
            'partner', 'partner_ref', 'debit', 'credit', 'balance',
            # 'partner_id'
        ]

    @api.model
    def _xls_arap_details_fields(self):
        """
        change list in custom module to add/drop columns or change order
        of the common part of the partner details table
        """
        return [
            'document', 'date', 'date_maturity', 'account', 'description',
            'rec_or_rec_part', 'debit', 'credit', 'balance',
            # 'partner_id',
        ]

    @api.model
    def _xls_ar_details_fields(self):
        """
        change list in custom module to add/drop columns or change order
        for the receivable details
        """
        return self._xls_arap_details_fields()

    @api.model
    def _xls_ap_details_fields(self):
        """
        change list in custom module to add/drop columns or change order
        for the receivable details
        """
        res = self._xls_arap_details_fields()
        res.insert(1, 'sup_inv_nr')
        return res

    @api.model
    def _xls_arap_overview_template(self):
        """
        Template updates, e.g.

        my_change = {
            'partner_id': {
                'header': [1, 20, 'text', _('Partner ID')],
                'lines': [1, 0, 'text', _render("p['p_id']")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}

    @api.model
    def _xls_arap_details_template(self):
        """
        Template updates
        """
        return {}
