# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//button[@name='action_invoice_cancel']")
            for node in nodes:
                node.attrib.pop('states', None)
                node.set(
                    'modifiers',
                    '{"invisible": '
                    '[["state", "not in", ["draft", "proforma2", "open"]], '
                    '["amount_total", "!=", 0]]}'
                )
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_invoice_cancel(self):
        for inv in self:
            if inv.state == 'paid' \
                    and inv.currency_id.is_zero(inv.amount_total):
                inv.action_cancel()
            else:
                super(AccountInvoice, inv).action_invoice_cancel()
        return True
