# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    accounting_date = fields.Date(
        string='Accounting Date',
        help="If set, the accounting entries created during the "
             "bank statement reconciliation process will be created "
             "at this date.\n"
             "This is useful if the accounting period in which the entries "
             "should normally be booked is already closed.")
    foreign_currency = fields.Boolean(
        compute='_compute_foreign_currency',
        store=True)

    @api.multi
    @api.depends('currency_id')
    def _compute_foreign_currency(self):
        for rec in self:
            if rec.currency_id != rec.company_id.currency_id:
                rec.foreign_currency = True
            else:
                rec.foreign_currency = False

    @api.multi
    def automatic_reconcile(self):
        reconcile_note = ''
        for st in self:
            reconcile_note += st._automatic_reconcile(
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
                'context': dict(self.env.context, note=reconcile_note),
                'type': 'ir.actions.act_window',
            }
        else:
            return True

    def _automatic_reconcile(self, reconcile_note='', st_lines=None):
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

    @api.multi
    def reconciliation_widget_preprocess(self):
        """
        This method as well as the javascript code calling this method
        has not been designed for inherit.
        In order to stay as close as possible to the standard code
        we have used the following trick:
        - in the javascript code we append the st_line_ids as negative
          values to the statement_ids
        - in this method we apply the statement lines passed to this method
          via this trick as a filter on the result
        This is not a good solution from a performance standpoint since
        all statement lines are browsed where we need only the selected ones.
        """
        statement_ids = self.ids
        if not statement_ids or statement_ids[-1] > 0:
            return super().reconciliation_widget_preprocess()
        for i, st_id in enumerate(statement_ids[::-1]):
            if st_id > 0:
                break
        cnt = len(statement_ids)
        st_line_ids = statement_ids[-i:]
        st_line_ids = [-x for x in st_line_ids]
        statements = self[:cnt - i]
        res = super(AccountBankStatement, statements).\
            reconciliation_widget_preprocess()
        res['st_lines_ids'] = st_line_ids
        return res
