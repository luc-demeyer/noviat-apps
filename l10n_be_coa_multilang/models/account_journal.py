# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _report_xlsx_fields(self):
        """
        Adapt list in inherited module to add/drop columns or change order
        """
        res = [
            'move_name',         # account.move,name
            'move_date',         # account.move,date
            'acc_code',          # account.account,code
            'partner_name',      # res.partner,name
            'aml_name',          # account.move.line,name
            'tax_code',          # account.tax.code,code
            'tax_amount',        # account.move.line,tax_amount
            'debit',             # account.move.line,debit
            'credit',            # account.move.line,credit
            'balance',           # debit-credit
            # 'date_maturity',   # account.move.line,date_maturity
            # 'full_reconcile',  # account.move.line,reconcile_id.name
            # 'reconcile_amount',
            # 'partner_ref',       # res.partner,ref
            # 'move_ref',          # account.move,ref
            # 'move_id',           # account.move,id
            # 'acc_name',          # account.account,name
            # 'journal',           # account.journal,name
            # 'journal_code',      # account.journal,code
            # 'analytic_account',       # account.analytic.account,name
            # 'analytic_account_code',  # account.analytic.account,code
        ]
        return res

    # Change/Add Template entries
    def _report_xlsx_template(self):
        """
        Template updates, e.g.

        my_change = {
            'move_name':{
                'header': [1, 20, 'text', _render("_('My Move Title')")],
                'lines': [1, 0, 'text', _render("l['move_name'] != '/' and
                l['move_name'] or ('*'+str(l['move_id']))")],
                'totals': [1, 0, 'text', None]},
        }
        return my_change
        """
        return {}
