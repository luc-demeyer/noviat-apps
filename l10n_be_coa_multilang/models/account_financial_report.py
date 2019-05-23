# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'

    code = fields.Char(size=16)
    invisible = fields.Boolean(
        help="Hide this entry from the printed report.")

    def _get_children_by_order(self):
        """
        The 'report.account.report_financial, get_account_lines' method
        does not allow to include extra fields in list of returned
        value dicts.
        We bypass this limitation by adding the 'code' to the 'name'
        field for the belgian reports in the cache.
        In Odoo 10.0 and initially also Odoo 11.0 we used the
        _convert_to_cache method to do this.
        The convert_to_cache technique doesn't work any more for this purpose
        as from 2019-02-04 (commit 36551615b7265ad83dbf9d1207ff9ee59b7069f3,
        [IMP] read, cache: faster read by updating the cache by fields)
        We now update the cache here.

        TODO:
        make PR to add an '_update_account_lines' method into the
        get_account_lines method so that this code can be replaced
        by a cleaner solution.
        """
        if self.env.context.get('get_children_by_sequence'):
            recs = self.search(
                [('id', 'child_of', self.ids[0]), ('invisible', '=', 0)],
                order='sequence ASC')
        else:
            recs = super()._get_children_by_order()
        if self.env.context.get('add_code_to_name'):
            field = self._fields['name']
            for r in recs:
                if r.code and r.name:
                    val = r.name + ' - (' + r.code + ')'
                    self.env.cache.set(r, field, val)
        return recs
