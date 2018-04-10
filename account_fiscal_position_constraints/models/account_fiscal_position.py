# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    company_id = fields.Many2one(
        required=True, default=lambda self: self.env.user.company_id)

    _sql_constraints = [(
        'name_company_uniq',
        'unique (name, company_id)',
        'The name of the fiscal position must be unique per company !')]

    @api.multi
    def unlink(self):
        for fpos in self:

            partners = self.env['res.partner'].with_context(
                active_test=False).search(
                    [('property_account_position_id', '=', fpos.id)])
            if partners:
                partner_list = [
                    '%s (ID:%s)' % (x.name, x.id) for x in partners]
                raise UserError(_(
                    "You cannot delete a fiscal position that "
                    "has been set on partner records"
                    "\nAs an alterative, you can disable a "
                    "fiscal position via the 'active' flag."
                    "\n\nPartner records: %s") % partner_list)

            invoices = self.env['account.invoice'].with_context(
                active_test=False).search(
                    [('fiscal_position_id', '=', fpos.id)])
            if invoices:
                invoice_list = [
                    '%s (ID:%s)' % (x.number or 'n/a', x.id)
                    for x in invoices]
                raise UserError(_(
                    "You cannot delete a fiscal position that "
                    "has been used on invoices"
                    "\nAs an alterative, you can disable a "
                    "fiscal position via the 'active' flag."
                    "\n\nInvoices: %s") % invoice_list)

        return super(AccountFiscalPosition, self).unlink()
