# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountInvoiceSplit(models.TransientModel):
    _name = 'account.invoice.split'
    _description = 'Split Invoice'

    invoice_line_ids = fields.Many2many(
        comodel_name='account.invoice.line',
        relation='account_invoice_split_invoice_line_rel',
        string='Invoice Lines')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(AccountInvoiceSplit, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=False)
        invoice_id = self._context.get('active_id')
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='invoice_line_ids']")
        for node in nodes:
            node.set('domain', "[('invoice_id', '=', %s)]" % invoice_id)
        res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def split_invoice(self):
        self.ensure_one()
        old_id = self._context.get('active_id')
        old = self.env['account.invoice'].browse(old_id)

        if len(old.invoice_line) == len(self.invoice_line_ids):
            raise UserError(
                "You cannot move all lines.")

        ctx = dict(self._context, account_invoice_split=True)
        new = old.with_context(ctx).copy()
        for line in self.invoice_line_ids:
            line.invoice_id = new
        invoices = old + new
        invoices.button_reset_taxes()

        for invoice in invoices:
            if invoice.amount_total < 0:
                raise UserError(_(
                    "The amount of the resulting invoices must be > 0."))

        # make link with sale order if sale is installed
        if 'sale.order' in self.env.registry:
            so = self.env['sale.order'].search(
                [('invoice_ids', 'in', old_id)])
            so.write({'invoice_ids': [(4, new.id)]})

        # make link with purchase order if purchase is installed
        if 'purchase.order' in self.env.registry:
            po = self.env['purchase.order'].search(
                [('invoice_ids', 'in', old_id)])
            po.write({'invoice_ids': [(4, new.id)]})

        views = {
            'out_invoice': 'action_invoice_tree1',
            'out_refund': 'action_invoice_tree3',
            'in_invoice': 'action_invoice_tree2',
            'in_refund': 'action_invoice_tree4',
        }
        view = self.env.ref('account.%s' % views.get(old.type))
        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'view': view.id,
            'target': 'current',
            'context': self._context,
            'domain': [('id', 'in', invoices._ids)],
            }
