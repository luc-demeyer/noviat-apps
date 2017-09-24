# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    reinvoice_key_id = fields.Many2one(
        comodel_name='account.reinvoice.key',
        string='Reinvoice Key', index=True)
    reinvoice_line_ids = fields.One2many(
        comodel_name='account.reinvoice.line',
        inverse_name='move_line_in_id', readonly=True,
        string='Reinvoice Line')
    reinvoice_line_count = fields.Integer(
        compute='_compute_reinvoice_line_count',
        string='# of reinvoice lines')

    @api.multi
    def unlink(self, **kwargs):
        for aml in self:
            out_inv_lines = aml.mapped(
                'reinvoice_line_ids.invoice_line_out_id')
            out_invs = out_inv_lines.mapped('invoice_id')
            noks = out_invs.filtered(
                lambda r: r.state != 'cancel')
            if noks:
                raise UserError(_(
                    "Operation not allowed since associated "
                    "outgoing invoices are not in state 'cancel'."
                    "\nInvoice IDs: %s")
                    % noks.ids)
        return super(AccountMoveLine, self).unlink(**kwargs)

    @api.one
    def _compute_reinvoice_line_count(self):
        self.reinvoice_line_count = len(self.reinvoice_line_ids)

    @api.multi
    def view_reinvoice_lines(self):
        self.ensure_one()
        action = {}
        arl_ids = [x.id for x in self.reinvoice_line_ids]
        if arl_ids:
            module = __name__.split('addons.')[1].split('.')[0]
            form = self.env.ref(
                '%s.account_reinvoice_line_form') % module
            if len(arl_ids) > 1:
                tree = self.env.ref(
                    '%s.account_reinvoice_line_tree') % module
                action.update({
                    'name': _('Reinvoice Lines'),
                    'view_mode': 'tree,form',
                    'views': [(tree.id, 'tree'), (form.id, 'form')],
                    'domain': [('id', 'in', arl_ids)],
                })
            else:
                action.update({
                    'name': _('Reinvoice Line'),
                    'view_mode': 'form',
                    'view_id': form.id,
                    'res_id': arl_ids[0],
                })
            action.update({
                'context': self._context,
                'view_type': 'form',
                'res_model': 'account.reinvoice.line',
                'type': 'ir.actions.act_window',
            })
        return action
