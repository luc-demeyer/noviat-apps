# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    total_line_amount = fields.Float(
        compute='_compute_total_line_amount',
        string="Sum amounts",
        help="Total of all individual amounts included in the "
             "Payment Order, irrespective of currencies")

    @api.multi
    @api.depends('line_ids')
    def _compute_total_line_amount(self):
        for order in self:
            order.total_line_amount = reduce(
                lambda x, y: x + y.amount_currency, order.line_ids, 0.0)

    @api.onchange('mode')
    def _onchange_mode(self):
        self.company_id = self.mode.company_id

    @api.multi
    def unlink(self):
        for order in self:
            if order.state == 'done':
                raise UserError(_(
                    "You can not remove a Payment Order "
                    "that has already been processed !"
                    "\nIf such an action is required, "
                    "you should first cancel the Order."))
        return super(PaymentOrder, self).unlink()

    def get_wizard(self, type):
        if type == 'iso20022':
            return 'account_pain', 'account_pain_create_action'
        else:
            return super(PaymentOrder, self).get_wizard(type)

    @api.multi
    def action_open(self, *args):
        for order in self:
            for line in order.line_ids:
                if line.amount_currency <= 0:
                    raise UserError(_(
                        "Unsupported Payment Instruction "
                        "in Payment Line %s.\n"
                        "The value '%s' is less than the "
                        "minimum value allowed."
                    ) % (line.name, line.amount_currency))
        return super(PaymentOrder, self).action_open(*args)

    @api.multi
    def button_undo_payment(self):
        for order in self:
            attachs = self.env['ir.attachment'].search(
                [('res_model', '=', 'payment.order'),
                 ('res_id', '=', order.id)])
            attachs.unlink()
            order.state = 'draft'
            order.delete_workflow()
            order.create_workflow()
        return True
