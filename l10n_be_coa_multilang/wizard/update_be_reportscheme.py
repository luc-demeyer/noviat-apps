# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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
from openerp.exceptions import except_orm
import logging
_logger = logging.getLogger(__name__)


class l10n_be_update_be_reportscheme(models.TransientModel):
    _name = 'l10n_be.update_be_reportscheme'
    _description = 'Update BNB/NBB financial reports configuration'

    note = fields.Text('Result', readonly=True)

    def _update_be_reportscheme(self):
        """"
        This method is executed when installing the module and will
        create/update the entries in the BNB/NBB legal report scheme.
        """
        note = ''
        upd_ctx = {'update_be_reportscheme': True}
        scheme_table = self.env['be.legal.financial.reportscheme'].search([])
        be_report_ids = [x.report_id.id for x in scheme_table]
        accounts = self.env['account.account'].with_context(upd_ctx).search(
            ['|', ('type', '!=', 'view'), '&', ('type', '=', 'view'),
             ('centralized', '=', True)]
            )

        # delete old reporting configuration
        account_ids = [x.id for x in accounts]
        self._cr.execute(
            "DELETE FROM account_account_financial_report "
            "WHERE report_line_id IN %s and account_id IN %s",
            (tuple(be_report_ids), tuple(account_ids)))

        # filter out children of centralized accounts
        centralized_accounts = accounts.filtered(
            lambda x: x.centralized and x.type == 'view')
        removes = self.env['account.account']
        for ca in centralized_accounts:
            config_errors = ca.child_id.filtered(lambda x: x.centralized)
            if config_errors:
                note += _("Configuration Error :\n\n")
                note += _("A centralized account that is a child of "
                          "a parent centralized account is not supported !\n"
                          "Please review the configuration settings of the "
                          "following account(s) and its parents: \n%s"
                          ) % ', '.join([x.code + ' - ' + x.name +
                                         ' (' + x.company_id.name + ')'
                                         for x in config_errors])
            removes += ca.child_id
        accounts = accounts - removes

        # filter out accounts that do not belong to a reporting group
        be_scheme_accounts = self.env['account.account']
        for account in accounts:
            for entry in scheme_table:
                if account.code[0:len(entry.account_group)] \
                        == entry.account_group:
                    be_scheme_accounts += account
                    break

        # write list of entries that are not included in
        # the BNB reports to the note field
        non_be_scheme_accounts = accounts - be_scheme_accounts
        if non_be_scheme_accounts:
            note += _("Following accounts are not included in "
                      "the legal Belgian Balance and P&L reports:\n\n")
            for acc in non_be_scheme_accounts:
                note += "Code: %s (id: %s), company: %s\n" \
                    % (acc.code, acc.id, acc.company_id.name)
            note += "\n"

        for account in be_scheme_accounts:
            be_report_entries = scheme_table.filtered(
                lambda x: account.code[
                    0:len(x.account_group)] == x.account_group)
            if len(be_report_entries) > 1:
                raise except_orm(
                    _("Configuration Error !"),
                    _("Configuration Error in the "
                      "Belgian Legal Financial Report Scheme."))
            be_report_id = be_report_entries and \
                be_report_entries.report_id.id
            account.financial_report_ids = [(4, be_report_id)]

        return note

    def update_be_reportscheme(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        self.env = api.Environment(cr, uid, context)
        note = self._update_be_reportscheme()
        if note:
            self.write(cr, uid, ids[0], {'note': note})
            view = self.env.ref(
                'l10n_be_coa_multilang.update_be_reportscheme_result_view')
            return {
                'name': _('Results'),
                'res_id': ids[0],
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'l10n_be.update_be_reportscheme',
                'view_id': False,
                'target': 'new',
                'views': [(view.id, 'form')],
                'type': 'ir.actions.act_window'}
        else:
            return {'type': 'ir.actions.act_window_close'}
