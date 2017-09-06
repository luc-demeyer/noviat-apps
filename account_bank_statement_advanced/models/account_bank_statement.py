# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from openerp import api, fields, models, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    period_id = fields.Many2one(domain=[('special', '=', False)])
    fiscalyear_id = fields.Many2one(
        string='Fiscal Year', related='period_id.fiscalyear_id',
        store=True, readonly=True)
    all_lines_reconciled = fields.Boolean(compute='_all_lines_reconciled')

    @api.one
    @api.depends('line_ids')
    def _all_lines_reconciled(self):
        """
        Replacement of this method without inherit.

        Standard account module logic:
        all([line.journal_entry_id.id or line.account_id.id
             for line in statement.line_ids])
        """
        self.all_lines_reconciled = True
        for line in self.line_ids:
            if line.amount and not line.journal_entry_id:
                self.all_lines_reconciled = False
                break

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):
        """
        Hide 'Reset to New' button.
        We use fields_view_get in stead of xml inherit since older
        databases may have been migrated without the view that
        adds the 'button_draft' button.
        """
        res = super(AccountBankStatement, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            form = etree.XML(res['arch'])
            for node in form.xpath("//button[@name='button_draft']"):
                node.set('modifiers', '{"invisible": true}')
            res['arch'] = etree.tostring(form)
        return res

    @api.multi
    def button_cancel(self):
        """
        Replace the account module button_cancel to allow
        cancel statements while preserving associated moves.
        """
        self.state = 'draft'
        return True

    @api.multi
    def automatic_reconcile(self):
        reconcile_note = ''
        for st in self:
            reconcile_note = self._automatic_reconcile(
                reconcile_note=reconcile_note)
        if reconcile_note:
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.bank_statement_automatic_reconcile_result_view_form'
                % module)
            return {
                'name': _("Automatic Reconcile remarks:"),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bank.statement.automatic.reconcile.result.view',
                'view_id': result_view.id,
                'target': 'new',
                'context': dict(self._context, note=reconcile_note),
                'type': 'ir.actions.act_window',
            }
        else:
            return True

    def _automatic_reconcile(self, reconcile_note):
        """
        placeholder for modules that implement automatic reconciliation, e.g.
        - l10n_be_coda_advanced
        """
        self.ensure_one()
        return reconcile_note
