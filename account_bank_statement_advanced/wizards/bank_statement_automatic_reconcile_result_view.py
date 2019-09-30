# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankStatementAutomaticReconcileResultView(models.TransientModel):
    _name = 'bank.statement.automatic.reconcile.result.view'
    _description = 'Transient Model to display Automatic Reconcile results'

    note = fields.Text(
        string='Notes', readonly=True,
        default=lambda self: self._context.get('note'))
