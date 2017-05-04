# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models, tools


class AccountJournalMultiCompanyList(models.Model):
    """
    Class to allow selection of Journals in target companies
    without hitting access violations.
    """
    _name = 'account.journal.multi.company.list'
    _description = 'SQL view on Journals'
    _auto = False

    name = fields.Char()
    code = fields.Char()
    type = fields.Char()
    company_id = fields.Char()

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'company_list_view')
        cr.execute("""
            CREATE OR REPLACE VIEW account_journal_multi_company_list AS (
            SELECT
                id, name, code, type, company_id::text AS company_id
            FROM
                account_journal
            )
        """)

    @api.multi
    def name_get(self):
        return [(j.id, ' - '.join([j.code, j.name])) for j in self]
