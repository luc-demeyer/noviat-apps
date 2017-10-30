# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import fields, orm
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def _amount_to_pay(self, cr, uid, ids, name, arg={}, context=None):
        """
        Return the amount still to pay regarding all the payment orders
        """
        if not ids:
            return {}
        amounts_residual = self.read(
            cr, uid, ids, ['amount_residual_currency'], context=context)
        cr.execute(
            "SELECT ml.id, "
            "  (SELECT coalesce(sum(amount_currency), 0) "
            "     FROM payment_line pl "
            "     INNER JOIN payment_order po "
            "       ON (pl.order_id = po.id) "
            "     WHERE move_line_id = ml.id "
            "       AND po.state != 'cancel' "
            "       AND pl.bank_statement_line_id IS NULL) AS pl_amount "
            "FROM account_move_line ml "
            "WHERE id IN %s", (tuple(ids), ))
        amounts_paylines = dict(cr.fetchall())
        amounts_to_pay = {}
        for entry in amounts_residual:
            k = entry['id']
            v = entry['amount_residual_currency'] - amounts_paylines[k]
            amounts_to_pay[k] = v
        return amounts_to_pay

    def _to_pay_search(self, cr, uid, obj, name, args, context=None):
        if not args:
            return []
        line_obj = self.pool['account.move.line']
        query = line_obj._query_get(cr, uid, context={'all_fiscalyear': True})
        query += 'AND l.blocked = False '
        where = ' and '.join(
            map(lambda x: """
                (SELECT
                CASE WHEN l.amount_currency < 0
                    THEN - l.amount_currency
                    ELSE l.credit
                END - coalesce(sum(pl.amount_currency), 0)
                FROM payment_line pl
                INNER JOIN payment_order po ON (pl.order_id = po.id)
                WHERE move_line_id = l.id
                AND po.state != 'cancel'
                AND pl.bank_statement_line_id IS NULL
                ) %(operator)s %%s """ % {'operator': x[1]},
                args))
        sql_args = tuple(map(itemgetter(2), args))

        cr.execute(
            "SELECT id FROM account_move_line l "
            "WHERE account_id IN "
            "(select id FROM account_account WHERE type in %s AND active) "
            "AND reconcile_id IS null AND credit > 0 AND " + where +
            " AND " + query,
            (('payable', 'receivable'), ) + sql_args)

        res = cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', map(lambda x:x[0], res))]

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if view_type == 'tree':
            mod_obj = self.pool.get('ir.model.data')
            if context is None:
                context = {}
            if context.get('account_payment', False):
                tree = 'account_move_line_view_tree_account_pain'
                model_data_ids = mod_obj.search(
                    cr, uid,
                    [('model', '=', 'ir.ui.view'),
                     ('name', '=', tree)],
                    context=context)
                view_id = mod_obj.read(
                    cr, uid, model_data_ids, fields=['res_id'],
                    context=context)[0]['res_id']
        return super(account_move_line, self).fields_view_get(
            cr, uid, view_id, view_type, context=context, toolbar=toolbar,
            submenu=submenu)

    _columns = {
        'amount_to_pay': fields.function(
            _amount_to_pay, method=True,
            type='float', string='Amount to pay', fnct_search=_to_pay_search),
        'supplier_direct_debit': fields.related(
            'invoice', 'supplier_direct_debit', type='boolean',
            relation='account.invoice',
            string='Supplier Direct Debit', readonly=True),
    }
