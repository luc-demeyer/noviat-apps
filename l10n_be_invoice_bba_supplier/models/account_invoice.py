# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    supplier_payment_ref_type = fields.Selection(
        selection='_selection_supplier_payment_ref_type',
        string='Payment Reference Type',
        required=True, default='normal')
    supplier_payment_ref = fields.Char(
        string='Payment Reference',
        help="Payment reference for use within payment orders.")

    @api.model
    def _selection_supplier_payment_ref_type(self):
        return [
            ('normal', _('Free Communication')),
            ('bba', _('BBA Structured Communication'))]

    @api.constrains('supplier_payment_ref_type', 'supplier_payment_ref')
    def _check_communication(self):
        for inv in self:
            if inv.supplier_payment_ref_type == 'bba' \
                    and not self.check_bbacomm(inv.supplier_payment_ref):
                raise ValidationError(
                    _("Invalid BBA Structured Communication !"))

    @api.onchange('supplier_payment_ref_type', 'reference')
    def _onchange_reference(self):
        if self.type == 'in_invoice' \
                and self.supplier_payment_ref_type == 'normal':
            self.supplier_payment_ref = self.reference

    @api.model
    def create(self, vals):
        if vals.get('supplier_payment_ref_type') == 'bba' \
                and self._context.get('type') == 'in_invoice':
            pay_ref = vals.get('supplier_payment_ref')
            if self.check_bbacomm(pay_ref):
                vals['supplier_payment_ref'] = self._format_bbacomm(pay_ref)
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def write(self, vals):
        for inv in self:
            if inv.state == 'draft':
                if 'supplier_payment_ref_type' in vals:
                    pay_ref_type = vals['supplier_payment_ref_type']
                else:
                    pay_ref_type = inv.supplier_payment_ref_type
                if pay_ref_type == 'bba':
                    if 'supplier_payment_ref' in vals:
                        bbacomm = vals['supplier_payment_ref']
                    else:
                        bbacomm = inv.supplier_payment_ref or ''
                    if self.check_bbacomm(bbacomm):
                        vals['supplier_payment_ref'] = self._format_bbacomm(
                            bbacomm)
        return super(AccountInvoice, self).write(vals)

    def _format_bbacomm(self, val):
        bba = re.sub('\D', '', val)
        bba = '+++%s/%s/%s+++' % (
            bba[0:3], bba[3:7], bba[7:])
        return bba
