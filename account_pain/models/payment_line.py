# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from lxml import etree
import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    name = fields.Char(string='Payment Line Ref.')
    state = fields.Selection(
        selection=[('normal', 'Free Communication'),
                   ('structured', 'Structured Communication')])
    struct_comm_type = fields.Selection(
        selection=lambda self: self._selection_struct_comm_type(),
        string='Structured Communication Type')

    @api.model
    def _selection_struct_comm_type(self):
        res = self.env['account.invoice'].fields_get(
            allfields=['reference_type'])['reference_type']['selection']
        res.pop([i for i, x in enumerate(res) if x[0] == 'none'][0])
        bba_list = [i for i, x in enumerate(res) if x[0] == 'bba']
        if not bba_list:
            res.append(('bba', 'BBA Structured Communication'))
        return res

    @api.multi
    @api.constrains('communication')
    def _check_communication(self):
        for line in self:
            if line.state == 'structured':
                if line.struct_comm_type == 'bba':
                    if not check_bba_comm(line.communication):
                        raise UserError(_(
                            "Invalid BBA Structured Communication !"))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(PaymentLine, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self._context.get('payment_line_readonly') \
                and view_type in ['tree', 'form']:
            doc = etree.XML(res['arch'])
            tree = doc.xpath("/tree")
            for node in tree:
                if 'editable' in node.attrib:
                    del node.attrib['editable']
            form = doc.xpath("/form")
            for el in [tree, form]:
                for node in el:
                    node.set('edit', 'false')
                    node.set('create', 'false')
                    node.set('delete', 'false')
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, vals):
        """
        structured communication of payment line is created
        by referencing an invoice
        """
        if 'move_line_id' in vals and vals['move_line_id']:
            move_line = self.env['account.move.line'].browse(
                vals['move_line_id'])
            inv = move_line.invoice
            if inv and inv.reference_type != 'none':
                vals['state'] = 'structured'
                vals['struct_comm_type'] = inv.reference_type
                vals['communication'] = inv.reference
        # verify correctness of bba structured communication
        # when created via the payment line form
        if 'state' in vals and (vals['state'] == 'structured'):
            if 'struct_comm_type' in vals \
                    and (vals['struct_comm_type'] == 'bba'):
                if 'communication' in vals:
                    bbacomm = vals['communication']
                    if check_bba_comm(bbacomm):
                        bbacomm = re.sub('\D', '', bbacomm)
                        vals['communication'] = \
                            '+++' + bbacomm[0:3] + '/' + bbacomm[3:7] + '/' \
                            + bbacomm[7:] + '+++'
                    else:
                        raise UserError(_(
                            "Payment Instruction Error !"
                            "\nInvalid BBA Structured Communication in "
                            "Payment Line %s, please correct !"
                        ) % vals['name'])
        pl = super(PaymentLine, self).create(vals)
        # code infra bypasses a bug in account_payment module:
        # when a payment line is created on a new, unsaved payment order
        # the company_id is empty
        if not pl.company_id:
            pl.company_id = pl.order_id.mode.company_id
        return pl

    @api.multi
    def write(self, vals):
        for line in self:
            line_state = vals.get('state') or line.state
            if line_state == 'structured':
                if 'struct_comm_type' in vals:
                    struct_comm_type = vals['struct_comm_type']
                else:
                    struct_comm_type = line.struct_comm_type or ''
                if struct_comm_type == 'bba':
                    if 'communication' in vals:
                        bbacomm = vals['communication']
                    else:
                        bbacomm = line.communication or ''
                    if check_bba_comm(bbacomm):
                        bbacomm = re.sub('\D', '', bbacomm)
                        vals['communication'] = \
                            '+++' + bbacomm[0:3] + '/' + bbacomm[3:7] + '/' \
                            + bbacomm[7:] + '+++'
                    else:
                        name = vals.get('name') or line.name
                        raise UserError(_(
                            "Payment Instruction Error !"
                            "\nInvalid BBA Structured Communication in "
                            "Payment Line %s, please correct !"
                        ) % name)
            super(PaymentLine, line).write(vals)
        return True


def check_bba_comm(val):
    supported_chars = '0-9+*/ '
    pattern = re.compile('[^' + supported_chars + ']')
    if pattern.findall(val or ''):
        return False
    bbacomm = re.sub('\D', '', val or '')
    if len(bbacomm) == 12:
        base = int(bbacomm[:10])
        mod = base % 97 or 97
        if mod == int(bbacomm[-2:]):
            return True
    return False
