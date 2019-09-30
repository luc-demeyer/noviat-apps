# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class l10n_be_update_be_reportscheme(models.TransientModel):
    _name = 'l10n_be.update_be_reportscheme'
    _description = 'Update BNB/NBB financial reports configuration'

    update_account_type = fields.Boolean(
        help="Update also Account Types")
    update_account_tags = fields.Boolean(
        help="Update also Account Tags")
    note = fields.Text('Result', readonly=True)

    def _update_be_reportscheme(self, company):
        """"
        This method is executed when installing the module and will
        create/update the entries in the BNB/NBB legal report scheme.
        """
        note = ''
        non_be_scheme_accounts = self.env['account.account']
        upd_ctx = {'update_be_reportscheme': True}
        if not self.update_account_type:
            upd_ctx.update({'noupdate_account_type': True})
        if not self.update_account_tags:
            upd_ctx.update({'noupdate_account_tags': True})
        accounts = self.env['account.account'].with_context(upd_ctx).search(
            [('company_id', '=', company.id)])
        for account in accounts:
            entry, entries = account._get_be_report_scheme_entry(account.code)
            if not entry:
                non_be_scheme_accounts += account
            else:
                account._onchange_code()
        # write list of entries that are not included in
        # the BNB reports to the note field
        if self.env.context.get('l10n.be.coa.multilang.config'):
            # avoid warning for unaffected earnings account
            # when running config wizard
            non_be_scheme_accounts = non_be_scheme_accounts.filtered(
                lambda r: r.code != '999999')
        if non_be_scheme_accounts:
            non_be_scheme_accounts = non_be_scheme_accounts.sorted(
                lambda r: r.code)
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
        country_codes = self.env['account.account']._get_be_scheme_countries()
        companies = self.env.user.company_ids.filtered(
            lambda r: r.country_id.code in country_codes)
        note = ''
        for company in companies:
            note = self._update_be_reportscheme(company)
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
