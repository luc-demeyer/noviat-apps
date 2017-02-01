# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models, _
from openerp.exceptions import Warning as UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def copy(self, default=None):
        if self._context.get('account_invoice_split'):
            default = {} if default is None else default.copy()
            default['invoice_line'] = []
            default['tax_line'] = []
        return super(AccountInvoice, self).copy(default=default)

    @api.multi
    def split_invoice(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_(
                "Only draft invoices can be splitted"))

        if len(self.invoice_line) < 2:
            raise UserError(_(
                "At least two invoice lines required for a split"))

        module = __name__.split('addons.')[1].split('.')[0]
        view = self.env.ref(
            '%s.account_invoice_split_view_form' % module)

        return {
            'name': _('Select Invoice Lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.split',
            'type': 'ir.actions.act_window',
            'view': view.id,
            'target': 'new',
            'context': self._context,
            }
