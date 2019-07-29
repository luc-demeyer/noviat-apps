# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    refund_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Refund Journal',
        domain="[('type', '=', type)]",
        help="Select the default Journal for Refunds created "
             "via the Refund Button.")
    refund_usage = fields.Selection(
        selection=[
            ('refund', 'Refunds'),
            ('regular', 'Regular'),
            ('both', 'Both')],
        default='both', required=True,
        help="Use this field to restrict the use of a Sale/Purchase "
             "to only refunds or only regular invoices.")

    @api.onchange('refund_usage')
    def _onchange_refund_usage(self):
        if self.refund_usage == 'refund':
            self.refund_sequence = True
        elif self.refund_usage == 'refund':
            self.refund_sequence = True

    @api.model
    def create(self, vals):
        self._refund_usage_vals(vals)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        self._refund_usage_vals(vals)
        return super().write(vals)

    def _refund_usage_vals(self, vals):
        """
        Update refund_sequence field since onchange not saved when readonly
        """
        if vals.get('refund_usage') == 'refund':
            vals['refund_sequence'] = True
