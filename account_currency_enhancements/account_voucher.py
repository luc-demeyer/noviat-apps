# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    def _check_paid(self, cr, uid, ids, name, args, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            ok = True
            for line in voucher.move_ids:
                #if (line.account_id.type, 'in', ('receivable', 'payable')) and not line.reconcile_id:
                if (line.account_id.type in ('receivable', 'payable')) and not line.reconcile_id: # FIX by Noviat
                    ok = False
            res[voucher.id] = ok
        return res

    _columns = {
        'paid': fields.function(_check_paid, string='Paid', type='boolean', help="The Voucher has been totally paid."),
    }

    def proforma_voucher(self, cr, uid, ids, context=None):
        if not context: context={}
        for voucher in self.browse(cr, uid, ids, context=context):
            company_id = voucher.company_id.id
        context['force_company'] = company_id
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher_brw.type in ('purchase', 'payment'):
            credit = voucher_brw.paid_amount_in_company_currency
        elif voucher_brw.type in ('sale', 'receipt'):
            debit = voucher_brw.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
                'name': voucher_brw.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': voucher_brw.account_id.id,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': voucher_brw.account_id.currency_id and current_currency or False,               # FIX by Noviat
                'amount_currency': voucher_brw.account_id.currency_id and sign * voucher_brw.amount or 0.0,    # FIX by Noviat
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due
            }
        return move_line

    def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
        '''
        Prepare the two lines in company currency due to currency rate difference.

        :param line: browse record of the voucher.line for which we want to create currency rate difference accounting
            entries
        :param move_id: Account move wher the move lines will be.
        :param amount_residual: Amount to be posted.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
        :rtype: tuple of dict
        '''
        amount_residual = (line.type == 'cr' and 1 or -1) * amount_residual # FIX by Noviat
        if amount_residual > 0:
            account_id = line.voucher_id.company_id.expense_currency_exchange_account_id
            if not account_id:
                raise osv.except_osv(_('Warning'),_("Unable to create accounting entry for currency rate difference. You have to configure the field 'Income Currency Rate' on the company! "))
        else:
            account_id = line.voucher_id.company_id.income_currency_exchange_account_id
            if not account_id:
                raise osv.except_osv(_('Warning'),_("Unable to create accounting entry for currency rate difference. You have to configure the field 'Expense Currency Rate' on the company! "))
        # Even if the amount_currency is never filled, we need to pass the foreign currency because otherwise
        # the receivable/payable account may have a secondary currency, which render this field mandatory
        account_currency_id = company_currency <> current_currency and current_currency or False
        move_line = {
            'journal_id': line.voucher_id.journal_id.id,
            'period_id': line.voucher_id.period_id.id,
            'name': _('change')+': '+(line.name or '/'),
            'account_id': line.account_id.id,
            'move_id': move_id,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': account_currency_id,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': amount_residual > 0 and amount_residual or 0.0,
            'debit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.voucher_id.date,
        }
        move_line_counterpart = {
            'journal_id': line.voucher_id.journal_id.id,
            'period_id': line.voucher_id.period_id.id,
            'name': _('change')+': '+(line.name or '/'),
            'account_id': account_id.id,
            'move_id': move_id,
            'amount_currency': 0.0,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': account_currency_id,
            'quantity': 1,
            'debit': amount_residual > 0 and amount_residual or 0.0,
            'credit': amount_residual < 0 and -amount_residual or 0.0,
            'date': line.voucher_id.date,
        }
        return (move_line, move_line_counterpart)


    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        voucher_brw = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        ctx = context.copy()
        ctx.update({'date': voucher_brw.date})
        for line in voucher_brw.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.amount:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher_brw.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                currency_rate_difference = line.move_line_id.amount_residual - amount
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': line.move_line_id.currency_id and line.move_line_id.currency_id.id or False, # FIX by Noviat
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher_brw.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher_brw.tax_id and voucher_brw.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher_brw.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                
                voucher_currency = voucher_brw.currency_id and voucher_brw.currency_id.id or voucher_brw.journal_id.company_id.currency_id.id
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id:    # FIX by Noviat 
                    # we compute the amount in that foreign currency. 
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    elif line.move_line_id.currency_id.id == voucher_brw.payment_rate_currency_id.id:
                        # if the rate is specified on the voucher, we must use it
                        voucher_rate = currency_obj.browse(cr, uid, voucher_currency, context=ctx).rate
                        amount_currency = (move_line['debit'] - move_line['credit']) * voucher_brw.payment_rate * voucher_rate
                    else:
                        # otherwise we use the rates of the system (giving the voucher date in the context)
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                        
                if line.amount == line.amount_unreconciled:
                    # this covers the case of a last payment (full reconcile) of an outstanding receivable/payable
                    if current_currency == company_currency:
                        # ensure full reconciliation both in foreign as well as company currency in case of last payment
                        # in company currency -> make amount_currency in new move line equal to amount_currency of
                        # open move line
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * line.move_line_id.amount_residual_currency
                    if line.move_line_id.currency_id.id == voucher_currency:
                        foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher_brw.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)

            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)

        return (tot_line, rec_lst_ids)

    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        acc_obj = self.pool.get('account.account')        
        move_line = {}

        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher_brw.currency_id or voucher_brw.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account = False
            write_off_name = ''
            if voucher_brw.payment_option == 'with_writeoff':
                account = voucher_brw.writeoff_acc_id
                write_off_name = voucher_brw.comment
            else:
                # FIX by Noviat : if no write_off account is specified we should the current AR or AP account
                cr.execute("SELECT aa.id FROM account_move_line aml " \
                    "INNER JOIN account_account aa ON aa.id = aml.account_id " \
                    "WHERE aml.move_id = %s AND aml.partner_id = %s AND aa.type IN ('payable', 'receivable')",
                    (move_id, voucher_brw.partner_id.id))
                ar_ap_ids = cr.fetchall()
                if len(ar_ap_ids) == 1:
                    account_id = ar_ap_ids[0][0]
                    account = acc_obj.browse(cr, uid, account_id)
                elif voucher_brw.type in ('sale', 'receipt'):
                    account = voucher_brw.partner_id.property_account_receivable
                else:
                    account = voucher_brw.partner_id.property_account_payable
            move_line = {
                'name': write_off_name or name,
                'account_id': account.id,
                'move_id': move_id,
                'partner_id': voucher_brw.partner_id.id,
                'date': voucher_brw.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': account.currency_id and voucher_brw.writeoff_amount or False,   # FIX by Noviat
                'currency_id': account.currency_id and account.currency_id.id or False,            # FIX by Noviat
                'analytic_account_id': voucher_brw.analytic_id and voucher_brw.analytic_id.id or False,
            }

        return move_line

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True

account_voucher() 

import netsvc

class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'
    
    def create_move_from_st_line(self, cr, uid, st_line_id, company_currency_id, next_number, context=None):
        voucher_obj = self.pool.get('account.voucher')
        wf_service = netsvc.LocalService("workflow")
        move_line_obj = self.pool.get('account.move.line')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        st_line = bank_st_line_obj.browse(cr, uid, st_line_id, context=context)
        if st_line.voucher_id:
            voucher_obj.write(cr, uid, [st_line.voucher_id.id], {'number': next_number}, context=context)
            if st_line.voucher_id.state == 'cancel':
                voucher_obj.action_cancel_draft(cr, uid, [st_line.voucher_id.id], context=context)
            wf_service.trg_validate(uid, 'account.voucher', st_line.voucher_id.id, 'proforma_voucher', cr)

            v = voucher_obj.browse(cr, uid, st_line.voucher_id.id, context=context)
            bank_st_line_obj.write(cr, uid, [st_line_id], {
                'move_ids': [(4, v.move_id.id, False)]
            })

            return move_line_obj.write(cr, uid, [x.id for x in v.move_ids], {'statement_id': st_line.statement_id.id}, context=context)
        return super(account_bank_statement, self).create_move_from_st_line(cr, uid, st_line.id, company_currency_id, next_number, context=context)

account_bank_statement() 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
