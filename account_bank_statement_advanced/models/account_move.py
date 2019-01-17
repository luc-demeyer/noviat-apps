# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_cancel(self):
        for move in self:
            for move_line in move.line_ids:
                st = move_line.statement_id
                if st and st.state == 'confirm':
                    raise UserError(
                        _("Operation not allowed ! "
                          "\nYou cannot unpost an Accounting Entry "
                          "that is linked to a Confirmed Bank Statement."))
        return super().button_cancel()
