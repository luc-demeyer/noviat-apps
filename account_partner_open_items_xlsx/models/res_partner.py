# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.addons.report_xlsx_helper.report.abstract_report_xlsx \
    import AbstractReportXlsx
_render = AbstractReportXlsx._render


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
    def _xls_open_items_overview_fields(self, report):
        """
        change list in custom module to add/drop columns or change order
        of the partner summary table
        """
        return [
            'partner', 'partner_ref',
            'amount_original', 'amount_reconciled', 'balance',
            # 'partner_id'
        ]

    @api.model
    def _xls_open_items_details_fields(self, report):
        """
        change list in custom module to add/drop columns or change order
        of the Open Items details table
        """
        wl = [
            'document', 'date', 'date_maturity', 'description',
            'amount_original', 'amount_reconciled', 'balance',
            'account', 'journal'
            # 'origin', 'partner_id',
        ]
        if report['type'] == 'payable':
            wl.insert(1, 'sup_inv_nr')
        return wl

    @api.model
    def _xls_open_items_overview_template(self, report):
        """
        Template updates, e.g.

        my_change = {
            'header': {
                'type': 'string',
                'value': self._('Partner ID'),
            },
            'lines': {
                'type': 'string',
                'value': self._render("p['p_id']"),
            },
            'width': 10,
        }
        res = super(ResPartner, self)._xls_open_items_overview_template()
        res.update(my_change)
        return res
        """
        return {}

    @api.model
    def _xls_open_items_details_template(self, report):
        """
        Template updates
        """
        return {}
