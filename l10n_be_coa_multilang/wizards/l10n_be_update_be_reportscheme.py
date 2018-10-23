# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
        be_reports = scheme_table.mapped('report_id')
        accounts = self.env[
            'account.account'].with_context(upd_ctx).search([])

        # filter out accounts that do not belong to a reporting group
        be_scheme_accounts = self.env['account.account']
        for account in accounts:
            for entry in scheme_table:
                if account.code[:len(entry.account_group)] \
                        == entry.account_group and entry.report_id:
                    be_scheme_accounts += account
                    break

        # delete old reporting configuration
        for account in be_scheme_accounts:
            updates = []
            old = account.financial_report_ids.filtered(
                lambda r: r in be_reports)
            if old:
                updates.append((3, old.id))
            be_report_entries = scheme_table.filtered(
                lambda x:
                account.code[:len(x.account_group)] == x.account_group)
            if len(be_report_entries) > 1:
                raise UserError(
                    _("Configuration Error !"),
                    _("Configuration Error in the "
                      "Belgian Legal Financial Report Scheme."))
            be_report = be_report_entries.report_id
            updates.append((4, be_report.id))
            account.financial_report_ids = updates

        # write list of entries that are not included in
        # the BNB reports to the note field
        non_be_scheme_accounts = accounts - be_scheme_accounts
        if self.env.context.get('l10n.be.coa.multilang.config'):
            # avoid warning for unaffected earnings account
            # when running config wizard
            non_be_scheme_accounts = non_be_scheme_accounts.filtered(
                lambda r: r.code != '999999')
        if non_be_scheme_accounts:
            note += _("Following accounts are not included in "
                      "the legal Belgian Balance and P&L reports:\n\n")
            for acc in non_be_scheme_accounts:
                note += "Code: %s (id: %s), company: %s\n" % (
                    acc.code, acc.id, acc.company_id.name)
            note += "\n"

        return note

    @api.multi
    def update_be_reportscheme(self):
        self.ensure_one()
        note = self._update_be_reportscheme()
        module = __name__.split('addons.')[1].split('.')[0]
        if note:
            self.note = note
            result_view = self.env.ref(
                '%s.%s_view_form_result' % (module, self._table))
            return {
                'name': _('Results'),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'target': 'new',
                'view_id': result_view.id,
                'type': 'ir.actions.act_window'}
        else:
            todo = self.env.ref('%s.%s_todo' % (module, self._table))
            todo.state = 'done'
            return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def button_close(self):
        self.ensure_one()
        module = __name__.split('addons.')[1].split('.')[0]
        todo = self.env.ref('%s.%s_todo' % (module, self._table))
        todo.state = 'done'
        return {'type': 'ir.actions.act_window_close'}
