# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tools.translate import _
from openerp.osv import fields, orm
from openerp import netsvc

import logging
_logger = logging.getLogger(__name__)


class payment_order(orm.Model):
    _inherit = 'payment.order'

    def _total_line_amount(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for order in self.browse(cursor, user, ids, context=context):
            if order.line_ids:
                res[order.id] = reduce(
                    lambda x, y: x + y.amount_currency, order.line_ids, 0.0)
            else:
                res[order.id] = 0.0
        return res

    _columns = {
        'total_line_amount': fields.function(
            _total_line_amount, string="Sum amounts", type='float',
            help="Total of all individual amounts included in the message, "
            "irrespective of currencies"),
    }

    def get_wizard(self, type):
        if type == 'iso20022':
            return 'account_pain', 'account_pain_create_action'
        else:
            return super(payment_order, self).get_wizard(type)

    def action_open(self, cr, uid, ids, *args):
        for payment in self.browse(cr, uid, ids):
            for line in payment.line_ids:
                if line.amount_currency <= 0:
                    raise orm.except_orm(
                        _('Payment Instruction Error!'),
                        _("Unsupported Payment Instruction "
                          "in Payment Line %s.\n"
                          "The value '%s' is less than the "
                          "minimum value allowed."
                          ) % (line.name, line.amount_currency))
        return super(payment_order, self).action_open(cr, uid, ids, *args)

    def unlink(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            if order.state == 'done':
                raise orm.except_orm(
                    _('Error'),
                    _("You can not remove a Payment Order "
                      "that has already been processed !"
                      "\nIf such an action is required, "
                      "you should first cancel the Order."))
        return super(payment_order, self).unlink(
            cr, uid, ids, context=context)

    def button_undo_payment(self, cr, uid, ids, context=None):
        att_obj = self.pool.get('ir.attachment')
        for order in self.browse(cr, uid, ids, context=context):
            att_ids = att_obj.search(
                cr, uid,
                [('res_model', '=', 'payment.order'),
                 ('res_id', '=', order.id)])
            if att_ids:
                att_obj.unlink(cr, uid, att_ids)
            self.write(cr, uid, order.id, {'state': 'draft'})
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_delete(uid, 'payment.order', order.id, cr)
            wf_service.trg_create(uid, 'payment.order', order.id, cr)
        return True
