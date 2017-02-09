# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tools.translate import _
from openerp.osv import fields, orm
import re
import logging
_logger = logging.getLogger(__name__)


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


class payment_line(orm.Model):
    _inherit = 'payment.line'

    def _get_struct_comm_types(self, cr, uid, context=None):
        res = self.pool.get('account.invoice').fields_get(
            cr, uid,
            ['reference_type'], context)['reference_type']['selection']
        res.pop([i for i, x in enumerate(res) if x[0] == 'none'][0])
        bba_list = [i for i, x in enumerate(res) if x[0] == 'bba']
        if not bba_list:
            res.append(('bba', 'BBA Structured Communication'))
        return res

    def _check_communication(self, cr, uid, ids):
        for line in self.browse(cr, uid, ids):
            if line.state == 'structured':
                if line.struct_comm_type == 'bba':
                    return check_bba_comm(line.communication)
        return True

    def fields_get(self, cr, uid, fields=None, context=None):
        fields = super(payment_line, self).fields_get(
            cr, uid, fields, context)
        if context is None:
            context = {}
        if context.get('payment_line_readonly'):
            for field in fields:
                fields[field]['readonly'] = True
        return fields

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('payment_line_readonly'):
            raise orm.except_orm(
                _('Warning'),
                _("Delete operation not allowed !"
                  "\nPlease go to the associated Payment Order "
                  "in order to delete this payment line"))
        return super(payment_line, self).unlink(cr, uid, ids, context=context)

    def create(self, cr, uid, vals, context=None):
        """
        structured communication of payment line is created
        by referencing an invoice
        """
        if 'move_line_id' in vals and vals['move_line_id']:
            move_line = self.pool.get('account.move.line').browse(
                cr, uid, vals['move_line_id'], context)
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
                        raise orm.except_orm(
                            _('Payment Instruction Error!'),
                            _("Invalid BBA Structured Communication in "
                              "Payment Line %s , please correct !")
                            % vals['name'])
        return super(payment_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if type(ids) is int:
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            vals2 = vals.copy()
            if 'state' in vals:
                line_state = vals['state']
            else:
                line_state = line.state
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
                        vals2['communication'] = \
                            '+++' + bbacomm[0:3] + '/' + bbacomm[3:7] + '/' \
                            + bbacomm[7:] + '+++'
                    else:
                        raise orm.except_orm(
                            _('Payment Instruction Error!'),
                            _("Invalid BBA Structured Communication in "
                              "Payment Line %s , please correct !")
                            % line.name)
            super(payment_line, self).write(cr, uid, [line.id], vals2, context)
        return True

    _columns = {
        'name': fields.char('Payment Line Ref.', size=64, required=True),
        'state': fields.selection(
            [('normal', 'Free Communication'),
             ('structured', 'Structured Communication')],
            'Communication Type', required=True),
        'struct_comm_type': fields.selection(
            _get_struct_comm_types, 'Structured Communication Type'),
    }
    _constraints = [
        (_check_communication,
         'Invalid BBA Structured Communication !',
         ['Communication']),
    ]
