# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    move_state = fields.Selection(
        related='move_id.state', string='Move State',
        readonly=True)

    @api.onchange('tax_code_id')
    def _onchange_tax_code_id(self):
        if self.tax_code_id:
            self.tax_amount = self.debit or self.credit or False
        else:
            self.tax_amount = False

    @api.multi
    def unlink(self, **kwargs):
        for move_line in self:
            st = move_line.statement_id
            if st and st.state == 'confirm':
                raise UserError(
                    _("Operation not allowed ! "
                      "\nYou cannot delete an Accounting Entry "
                      "that is linked to a Confirmed Bank Statement."))
        return super(AccountMoveLine, self).unlink(**kwargs)

    @api.multi
    def write(self, vals, **kwargs):
        for move_line in self:
            st = move_line.statement_id
            if st and st.state == 'confirm':
                for k in vals:
                    if k not in ['reconcile_id', 'reconcile_partial_id']:
                        raise UserError(
                            _("Operation not allowed ! "
                              "\nYou cannot modify an Accounting Entry "
                              "that is linked to a Confirmed Bank Statement. "
                              "\nStatement = %s"
                              "\nMove = %s (id:%s)\nUpdate Values = %s")
                            % (st.name, move_line.move_id.name,
                               move_line.move_id.id, vals))
        return super(AccountMoveLine, self).write(
            vals, **kwargs)
