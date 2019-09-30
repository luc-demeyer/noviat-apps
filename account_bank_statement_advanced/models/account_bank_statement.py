# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

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
        Placeholder for modules that implement automatic reconciliation (e.g.
        l10n_be_coda_advanced) as a preprocessing step before entering
        into the standard addons javascript reconciliation screen.
        This screen has also an 'auto_reconcile' option but unfortunately
        - too much hardcoded
        - risks on wrong reconciles
        - too late in the process (the javascript screen is not usable for
          lorge statements hence pre-processing is required)
        """
        self.ensure_one()
        return reconcile_note
