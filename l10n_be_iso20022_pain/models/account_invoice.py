# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    reference_type = fields.Selection(
        selection='_selection_reference_type')

    @api.model
    def _selection_reference_type(self):
        """
        This field is defined in the two 'depends' modules with inconsistency
        on selection list.
        TODO: make PR towards OCA account_payment_order to fix conflict
        """
        return [
            ('none', _('Free Communication')),
            ('bba', _('BBA Structured Communication')),
            ('structured', _('Structured Reference'))]
