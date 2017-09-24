# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(AccountInvoice, self).line_get_convert(
            cr, uid, x, part, date, context=context)
        if x.get('reinvoice_key_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['reinvoice_key_id'] = x['reinvoice_key_id']
        return res

    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super(AccountInvoice, self).inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('reinvoice_key_id', 'False')
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    reinvoice_key_id = fields.Many2one(
        comodel_name='account.reinvoice.key',
        string='Reinvoice Key', index=True)
    reinvoice_line_ids = fields.One2many(
        comodel_name='account.reinvoice.line',
        inverse_name='invoice_line_out_id', readonly=True,
        string='Reinvoice Lines')

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.reinvoice_key_id:
            res['reinvoice_key_id'] = line.reinvoice_key_id.id
        return res
