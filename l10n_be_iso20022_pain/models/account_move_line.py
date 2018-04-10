# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        """
        TODO:
        Make PR on OCA account_payment_order
        to support supplier_payment_ref field.
        Until such a PR is made and merged we postprocess
        the vals from this method.
        """
        vals = super(AccountMoveLine, self).\
            _prepare_payment_line_vals(payment_order)
        inv = self.invoice_id
        if hasattr(inv, 'supplier_payment_ref'):
            vals['communication_type'] = inv.supplier_payment_ref_type \
                or vals['communication_type']
            vals['communication'] = inv.supplier_payment_ref \
                or vals['communication']
        if vals['communication_type'] == 'bba':
            bbacomm = vals['communication'].replace('+', '').replace('/', '')
            if not inv.check_bbacomm(bbacomm):
                raise ValidationError(
                    _("Invalid BBA Structured Communication !"))
            vals['communication'] = bbacomm
        return vals
