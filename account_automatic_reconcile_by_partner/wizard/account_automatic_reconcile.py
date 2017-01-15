# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountAutomaticReconcile(models.TransientModel):
    _inherit = 'account.automatic.reconcile'

    partner_ids = fields.Many2many(
        string='Partners',
        comodel_name='res.partner',
        relation='reconcile_partner_rel',
        column1='reconcile_id',
        column2='partner_id')
    reconcile_all = fields.Boolean(
        help="Select this option in order to reconcile all "
             "open transactions for a partner when the "
             "total Debit sum is equal to the total "
             "Credit sum")

    @api.multi
    def reconcile_by_partner(self):
        """
        This method replaces the 'reconcile' method of the
        'account.automatic.reconcile' wizard in standard addons.
        """
        self.ensure_one()

        if not self.account_ids:
            raise UserError(_(
                "You must select accounts to reconcile."))

        reconciled = unreconciled = 0

        for account in self.account_ids:
            (rec, unrec) = self._reconcile_account(account)
            reconciled += rec
            unreconciled += unrec

        if self.reconcile_all:
            rec = self._reconcile_all()
            reconciled += rec
            unreconciled -= rec

        if self.partner_ids:
            unreconciled += self._get_remaining_unreconciled()

        self.reconciled = reconciled
        self.unreconciled = unreconciled
        ctx = dict(self._context,
                   reconciled=reconciled, unreconciled=unreconciled)
        wiz_view = self.env.ref('account.account_automatic_reconcile_view1')
        act = {
            'name': _("Result"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': wiz_view.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
        return act

    def _reconcile_account(self, account):
        """
        Logic copied from 'account.automatic.reconcile' wizard
        in standard addons.
        """

        partners = self.partner_ids
        if not partners:
            self._cr.execute(
                "SELECT partner_id FROM account_move_line "
                "WHERE account_id = %s AND reconcile_id IS NULL "
                "AND state != 'draft'",
                (account.id,))
            p_ids = [id for (id,) in self._cr.fetchall()]
            p_ids = list(set(p_ids))
            partners = self.env['res.partner'].browse(p_ids)

        reconciled = unreconciled = 0

        # step 1: auto-reconcile zero amount transactions
        self._cr.execute(
            "SELECT id FROM account_move_line "
            "WHERE account_id = %s AND partner_id IN %s "
            "AND reconcile_id IS NULL AND state != 'draft' "
            "AND coalesce(debit, 0.0) = 0.0 "
            "AND coalesce(credit, 0.0) = 0.0 ",
            (account.id, partners._ids))
        aml_ids = [id for (id,) in self._cr.fetchall()]
        for aml_id in aml_ids:
            aml = self.env['account.move.line'].browse(aml_id)
            aml.reconcile()
        reconciled += len(aml_ids)

        for partner in partners:

            # get unreconciled debit transactions for this partner
            self._cr.execute(
                "SELECT id, debit FROM account_move_line "
                "WHERE account_id = %s AND partner_id=%s "
                "AND reconcile_id IS NULL AND state != 'draft' "
                "AND debit > 0 "
                "ORDER BY date_maturity",
                (account.id, partner.id))
            debits = self._cr.fetchall()

            # get unreconciled credit transactions for this partner
            self._cr.execute(
                "SELECT id, credit FROM account_move_line "
                "WHERE account_id=%s AND partner_id=%s "
                "AND reconcile_id IS NULL AND state != 'draft' "
                "AND credit > 0 "
                "ORDER BY date_maturity",
                (account.id, partner.id))
            credits = self._cr.fetchall()

            max_amount = self.allow_write_off and self.max_amount or 0.0
            (rec, unrec) = self._do_reconcile(
                credits, debits, max_amount)
            reconciled += rec
            unreconciled += unrec

        return reconciled, unreconciled

    def _get_remaining_unreconciled(self):
        """
        add the number of transactions for partners with
        unreconciled transactions to the unreconciled count
        """
        partner_filter = self.partner_ids and 'AND partner_id not in (%s)' \
            % ','.join(map(str, filter(None, self.partner_ids._ids))) or ''
        unreconciled = 0
        for account in self.account_ids:
            self._cr.execute(
                "SELECT count(*) "
                "FROM account_move_line "
                "WHERE account_id = %s "
                "AND reconcile_id IS NULL "
                "AND state != 'draft' " + partner_filter,
                (account.id,))
            unreconciled += self._cr.fetchone()[0]
        return unreconciled

    def _do_reconcile(self, credits, debits, max_amount):
        """
        for one value of a credit, check all debits, and combination of them
        depending on the power. It starts with a power of one and goes up
        to the max power allowed.

        Logic copied from 'account.automatic.reconcile' wizard
        in standard addons.
        """
        def check2(value, move_list, power):
            def check(value, move_list, power):
                for i in range(len(move_list)):
                    move = move_list[i]
                    if power == 1:
                        if abs(value - move[1]) <= max_amount + 0.00001:
                            return [move[0]]
                    else:
                        del move_list[i]
                        res = check(value - move[1], move_list, power-1)
                        move_list[i:i] = [move]
                        if res:
                            res.append(move[0])
                            return res
                return False

            for p in range(1, power+1):
                res = check(value, move_list, p)
                if res:
                    return res
            return False

        def check4(list1, list2, power):
            """
            for a list of credit and debit and a given power, check if there
            are matching tuples of credit and debits, check all debits,
            and combination of them depending on the power.
            It starts with a power of one and goes up
            to the max power allowed.
            """
            def check3(value, list1, list2, list1power, power):
                for i in range(len(list1)):
                    move = list1[i]
                    if list1power == 1:
                        res = check2(value + move[1], list2, power - 1)
                        if res:
                            return ([move[0]], res)
                    else:
                        del list1[i]
                        res = check3(value + move[1], list1, list2,
                                     list1power-1, power-1)
                        list1[i:i] = [move]
                        if res:
                            x, y = res
                            x.append(move[0])
                            return (x, y)
                return False

            for p in range(1, power):
                res = check3(0, list1, list2, p, power)
                if res:
                    return res
            return False

        def check5(list1, list2, max_power):
            for p in range(2, max_power+1):
                res = check4(list1, list2, p)
                if res:
                    return res
            return False

        ok = True
        reconciled = 0
        while credits and debits and ok:
            res = check5(credits, debits, self.power)
            if res:
                debit_amls = self.env['account.move.line'].browse(res[1])
                credit_amls = self.env['account.move.line'].browse(res[0])
                amls = debit_amls + credit_amls
                if self.allow_write_off:
                    date_p = self.period_id.date_stop
                    ctx = dict(self._context, date_p=date_p)
                    amls.with_context(ctx).reconcile(
                        writeoff_acc_id=self.writeoff_acc_id.id,
                        writeoff_period_id=self.period_id.id,
                        writeoff_journal_id=self.journal_id.id)
                else:
                    debit_amounts = [x[1] for x in debits if x[0] in res[1]]
                    total_debit = reduce(lambda x, y: x + y, debit_amounts)
                    credit_amounts = [x[1] for x in credits if x[0] in res[0]]
                    total_credit = reduce(lambda x, y: x + y, credit_amounts)
                    diff = total_debit - total_credit
                    if amls[0].company_id.currency_id.is_zero(diff):
                        amls.reconcile()
                reconciled += len(amls)
                credits = [(id, credit) for (id, credit) in credits
                           if id not in res[0]]
                debits = [(id, debit) for (id, debit) in debits
                          if id not in res[1]]
            else:
                ok = False
        return (reconciled, len(credits)+len(debits))

    def _reconcile_all(self):
        """
        logic infra copied from standard addons.

        reconcile automatically all transactions
        from partners whose remaining balance is 0
        """
        reconciled = 0

        select = "SELECT partner_id FROM account_move_line"
        where = "WHERE account_id = %s AND reconcile_id IS NULL " \
            "AND state != 'draft'"
        if self.partner_ids:
            where += " AND partner_id IN %s"
        groupby = "GROUP BY partner_id"
        if not self.allow_write_off:
            having = "HAVING ABS(SUM(debit-credit)) = 0.0 "
        else:
            having = "HAVING ABS(SUM(debit-credit)) <= %s " \
                % self.max_amount
        having += "AND count(*) > 0 "

        for account_id in self.account_ids:
            params = (account_id.id,)
            if self.partner_ids:
                params += (self.partner_ids._ids,)
            query = ' '.join([select, where, groupby, having])
            self._cr.execute(query, params)
            partner_ids = [id for (id,) in self._cr.fetchall()]
            for partner_id in partner_ids:
                self._cr.execute(
                    "SELECT id FROM account_move_line "
                    "WHERE account_id = %s "
                    "AND partner_id = %s "
                    "AND state != 'draft' "
                    "AND reconcile_id IS NULL",
                    (account_id.id, partner_id))
                aml_ids = [id for (id,) in self._cr.fetchall()]
                if aml_ids:
                    reconciled += len(aml_ids)
                    amls = self.env['account.move.line']. browse(aml_ids)
                    if self.allow_write_off:
                        amls.reconcile(
                            writeoff_acc_id=self.writeoff_acc_id.id,
                            writeoff_period_id=self.period_id.id,
                            writeoff_journal_id=self.journal_id.id)
                    else:
                        amls.reconcile()
        return reconciled
