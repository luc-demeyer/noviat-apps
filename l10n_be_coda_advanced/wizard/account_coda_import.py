# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import re
import time
import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from sys import exc_info
from traceback import format_exception

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .coda_helpers import \
    calc_iban_checksum, check_bban, check_iban, get_iban_and_bban, \
    repl_special, str2date, str2time, list2float, number2float

_logger = logging.getLogger(__name__)

INDENT = '\n' + 8 * ' '
ST_LINE_NAME_FAMILIES = ['13', '35', '41', '80']
PARSE_COMMS_MOVE = [
    '100', '101', '102', '103', '105', '106', '107', '108', '111', '113',
    '114', '115', '121', '122', '123', '124', '125', '126', '127']
PARSE_COMMS_INFO = [
    '001', '002', '004', '005', '006', '007',
    '107', '008', '009', '010', '011']


class AccountCodaImport(models.TransientModel):
    _name = 'account.coda.import'
    _description = 'Import CODA File'

    coda_data = fields.Binary(
        string='CODA (Zip) File', required=True)
    coda_fname = fields.Char(
        string='CODA Filename', default='', required=True)
    coda_fname_dummy = fields.Char(
        related='coda_fname', string='CODA Filename', readonly=True)
    accounting_date = fields.Date(
        help="Keep empty to use the date in the CODA File")
    reconcile = fields.Boolean(
        help="Launch Automatic Reconcile after CODA import.", default=True)
    skip_undefined = fields.Boolean(
        help="Skip Bank Statements for accounts which have not been defined "
             "in the CODA configuration.", default=True)
    note = fields.Text(string='Log')

    @api.onchange('coda_data')
    def onchange_fdata(self):
        self.coda_fname_dummy = self.coda_fname

    @api.model
    def _check_account_payment(self):
        res = self.env['ir.module.module'].search(
            [('name', '=', 'account_payment'), ('state', '=', 'installed')])
        return res and True or False

    def _coda_record_0(self, coda_statement, line, coda_parsing_note):

        coda_version = line[127]
        if coda_version not in ['1', '2']:
            err_string = _(
                "\nCODA V%s statements are not supported, "
                "please contact your bank !") % coda_version
            raise UserError(err_string)
        coda_statement['coda_version'] = coda_version
        coda_statement['coda_transactions'] = {}
        coda_statement['date'] = str2date(line[5:11])
        coda_statement['coda_creation_date'] = str2date(line[5:11])
        coda_statement['bic'] = line[60:71].strip()
        coda_statement['separate_application'] = line[83:88]
        coda_statement['first_transaction_date'] = False
        coda_statement['state'] = 'draft'
        coda_statement['coda_note'] = ''
        coda_statement['skip'] = False
        coda_statement['main_move_stack'] = []
        coda_statement['glob_lvl_stack'] = [0]
        return coda_parsing_note

    def _coda_record_1(self, coda_statement, line, coda_parsing_note):

        skip = False
        coda_statement['currency'] = 'EUR'  # default currency
        if coda_statement['coda_version'] == '1':
            coda_statement['acc_number'] = line[5:17]
            if line[18:21].strip():
                coda_statement['currency'] = line[18:21]
        elif line[1] == '0':  # Belgian bank account BBAN structure
            coda_statement['acc_number'] = line[5:17]
            coda_statement['currency'] = line[18:21]
        elif line[1] == '1':  # foreign bank account BBAN structure
            coda_statement['acc_number'] = line[5:39].strip()
            coda_statement['currency'] = line[39:42]
        elif line[1] == '2':  # Belgian bank account IBAN structure
            coda_statement['acc_number'] = line[5:21]
            coda_statement['currency'] = line[39:42]
        elif line[1] == '3':  # foreign bank account IBAN structure
            coda_statement['acc_number'] = line[5:39].strip()
            coda_statement['currency'] = line[39:42]
        else:
            err_string = _("\nUnsupported bank account structure !")
            raise UserError(err_string)
        coda_statement['description'] = line[90:125].strip()

        def cba_filter(coda_bank):
            acc_number = coda_bank.bank_id.sanitized_acc_number
            if acc_number:
                cba_numbers = get_iban_and_bban(acc_number)
                cba_currency = coda_bank.currency_id.name
                cba_descriptions = [
                    coda_bank.description1 or '',
                    coda_bank.description2 or '']
                if coda_statement['acc_number'] in cba_numbers \
                        and coda_statement['currency'] == cba_currency \
                        and coda_statement['description'] in cba_descriptions:
                    return True
            return False

        cba = filter(cba_filter, self._coda_banks)

        if cba:
            cba = cba[0]
            coda_statement['coda_bank_params'] = cba
            self._company_bank_accounts = \
                cba.company_id.bank_journal_ids.mapped(
                    'bank_account_id').mapped('sanitized_acc_number')
        else:
            if self.skip_undefined:
                self._coda_import_note += _(
                    "\n\nNo matching CODA Bank Account Configuration "
                    "record found !") + \
                    _("\nPlease check if the 'Bank Account Number', "
                      "'Currency' and 'Account Description' fields "
                      "of your configuration record match with"
                      " '%s', '%s' and '%s' if you need to import "
                      "statements for this Bank Account Number !"
                      ) % (coda_statement['acc_number'],
                           coda_statement['currency'],
                           coda_statement['description'])
                skip = True
            else:
                err_string = _(
                    "\nNo matching CODA Bank Account Configuration "
                    "record found !") + \
                    _("\nPlease check if the 'Bank Account Number', "
                      "'Currency' and 'Account Description' fields "
                      "of your configuration record match with"
                      " '%s', '%s' and '%s' !"
                      ) % (coda_statement['acc_number'],
                           coda_statement['currency'],
                           coda_statement['description'])
                raise UserError(err_string)
        bal_start = list2float(line[43:58])  # old balance data
        if line[42] == '1':  # 1= Debit
            bal_start = - bal_start
        coda_statement['balance_start'] = bal_start
        coda_statement['old_balance_date'] = str2date(line[58:64])
        coda_statement['acc_holder'] = line[64:90]
        coda_statement['paper_ob_seq_number'] = line[2:5]
        coda_statement['coda_seq_number'] = line[125:128]

        if skip:
            coda_statement['skip'] = skip
            return coda_parsing_note

        # we already initialise the coda_statement['name'] field
        # with the currently available date
        # in case an 8 record is present, this data will be updated
        if cba.coda_st_naming:
            coda_statement['name'] = cba.coda_st_naming % {
                'code': cba.journal_id.code or '',
                'year': coda_statement['date'][:4],
                'y': coda_statement['date'][2:4],
                'coda': coda_statement['coda_seq_number'],
                'paper_ob': coda_statement['paper_ob_seq_number'],
                'paper': coda_statement['paper_ob_seq_number'],
            }
            # We have to skip the already processed statements
            # when we reprocess CODA file
            if self._coda_id:
                old_statements = self.env['account.bank.statement'].search(
                    [('coda_id', '=', self._coda_id),
                     ('name', '=', coda_statement['name'])])
                if old_statements:
                    skip = True
        else:
            coda_statement['name'] = '/'
        # hook to allow further customisation
        if not skip:
            self._coda_statement_init_hook(coda_statement)
        coda_statement['skip'] = skip

        return coda_parsing_note

    def _coda_record_2(self, coda_statement, line, coda_parsing_note,
                       transaction_seq):

        if line[1] == '1':
            coda_parsing_note, transaction_seq = self._coda_record_21(
                coda_statement, line, coda_parsing_note, transaction_seq)

        elif line[1] == '2':
            coda_parsing_note = self._coda_record_22(
                coda_statement, line, coda_parsing_note, transaction_seq)

        elif line[1] == '3':
            coda_parsing_note = self._coda_record_23(
                coda_statement, line, coda_parsing_note, transaction_seq)

        else:
            # movement data record 2.x (x <> 1,2,3)
            err_string = _(
                "\nMovement data records of type 2.%s are not supported !"
            ) % line[1]
            raise UserError(err_string)

        return coda_parsing_note, transaction_seq

    def _coda_record_21(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        # list of lines parsed already
        coda_transactions = coda_statement['coda_transactions']

        transaction = {}
        transaction_seq = transaction_seq + 1
        transaction['sequence'] = transaction_seq
        transaction['type'] = 'regular'
        transaction['trans_family'] = False
        transaction['struct_comm_type'] = ''
        transaction['struct_comm_type_id'] = False
        transaction['struct_comm_type_desc'] = ''
        transaction['struct_comm_bba'] = ''
        transaction['communication'] = ''
        transaction['payment_reference'] = ''
        transaction['creditor_reference_type'] = ''
        transaction['creditor_reference'] = ''
        transaction['partner_name'] = ''
        transaction['counterparty_bic'] = ''
        transaction['counterparty_number'] = ''
        transaction['counterparty_currency'] = ''
        transaction['glob_lvl_flag'] = False
        transaction['globalisation_amount'] = False
        transaction['amount'] = 0.0

        transaction['ref'] = line[2:10]
        transaction['ref_move'] = line[2:6]
        transaction['ref_move_detail'] = line[6:10]

        main_move_stack = coda_statement['main_move_stack']
        previous_main_move = main_move_stack and main_move_stack[-1] or False
        main_move_stack_pop = True

        if main_move_stack \
                and transaction['ref_move'] != main_move_stack[-1]['ref_move']:
            # initialise main_move_stack
            # used to link 2.1 detail records to 2.1 main record
            # The main_move_stack contains the globalisation level move
            # or moves (in case of multiple levels)
            # plus the previous transaction move.
            main_move_stack = []
            main_move_stack_pop = False
            coda_statement['main_move_stack'] = main_move_stack
            # initialise globalisation stack
            coda_statement['glob_lvl_stack'] = [0]

        if main_move_stack:
            if main_move_stack[-1]['type'] == 'globalisation':
                transaction['glob_sequence'] = main_move_stack[-1]['sequence']
            elif main_move_stack[-1].get('glob_sequence'):
                transaction['glob_sequence'] = \
                    main_move_stack[-1]['glob_sequence']

        glob_lvl_stack = coda_statement['glob_lvl_stack']
        glob_lvl_stack_pop = False
        glob_lvl_stack_append = False

        transaction['trans_ref'] = line[10:31]
        transaction_amt = list2float(line[32:47])
        if line[31] == '1':    # 1=debit
            transaction_amt = -transaction_amt

        transaction['trans_type'] = line[53]
        trans_type = filter(
            lambda x: transaction['trans_type'] == x.type,
            self._trans_types)
        if not trans_type:
            err_string = _(
                "\nThe File contains an invalid CODA Transaction Type : %s !"
            ) % transaction['trans_type']
            raise UserError(err_string)
        transaction['trans_type_id'] = trans_type[0].id
        transaction['trans_type_desc'] = trans_type[0].description

        # processing of amount depending on globalisation
        glob_lvl_flag = int(line[124])
        transaction['glob_lvl_flag'] = glob_lvl_flag
        if glob_lvl_flag > 0:
            if glob_lvl_stack and glob_lvl_stack[-1] == glob_lvl_flag:
                transaction['amount'] = transaction_amt
                glob_lvl_stack_pop = True
            else:
                transaction['type'] = 'globalisation'
                transaction['amount'] = 0.0
                transaction['globalisation_amount'] = transaction_amt
                main_move_stack_pop = False
                glob_lvl_stack_append = True
        else:
            transaction['amount'] = transaction_amt
            if previous_main_move and previous_main_move['glob_lvl_flag'] > 0:
                main_move_stack_pop = False

        # The 'globalisation' concept can also be implemented
        # without the globalisation level flag.
        # This is e.g. used by Europabank to give the details of
        # Card Payments.
        if previous_main_move and \
                transaction['ref_move'] == previous_main_move['ref_move']:
            if transaction['ref_move_detail'] == '9999':
                # Current CODA parsing logic doesn't
                # support > 9999 detail lines
                err_string = _(
                    '\nTransaction Detail Limit reached !')
                raise UserError(err_string)
            elif transaction['ref_move_detail'] != '0000':
                if glob_lvl_stack[-1] == 0 \
                        and previous_main_move['type'] != 'globalisation':
                    # promote associated move record
                    # into a globalisation
                    glob_lvl_flag = 1
                    glob_lvl_stack_append = True
                    k = previous_main_move['sequence']
                    to_promote = coda_transactions[k]
                    if not previous_main_move.get('detail_cnt'):
                        to_promote.update({
                            'type': 'globalisation',
                            'glob_lvl_flag': glob_lvl_flag,
                            'globalisation_amount':
                                previous_main_move['amount'],
                            'amount': 0.0,
                            'account_id': False})
                        previous_main_move['promoted'] = True
                    main_move_stack_pop = False
                if not previous_main_move.get('detail_cnt'):
                    previous_main_move['detail_cnt'] = 1
                else:
                    previous_main_move['detail_cnt'] += 1

        # positions 48-53 : Value date or 000000 if not known (DDMMYY)
        transaction['val_date'] = str2date(line[47:53])
        # positions 54-61 : transaction code
        transaction['trans_family'] = line[54:56]
        trans_family = filter(
            lambda x: (x.type == 'family') and (
                x.code == transaction['trans_family']),
            self._trans_codes)
        if not trans_family:
            err_string = _(
                "\nThe File contains an invalid "
                "CODA Transaction Family : %s !"
            ) % transaction['trans_family']
            raise UserError(err_string)
        trans_family = trans_family[0]
        transaction['trans_family_id'] = trans_family.id
        transaction['trans_family_desc'] = trans_family.description
        transaction['trans_code'] = line[56:58]
        trans_code = filter(
            lambda x:
            (x.type == 'code') and (x.code == transaction['trans_code']) and
            (trans_family.id == x.parent_id.id),
            self._trans_codes)
        if trans_code:
            transaction['trans_code_id'] = trans_code[0].id
            transaction['trans_code_desc'] = trans_code[0].description
        else:
            transaction['trans_code_id'] = None
            transaction['trans_code_desc'] = _(
                "Transaction Code unknown, "
                "please consult your bank.")
        transaction['trans_category'] = line[58:61]
        trans_category = filter(
            lambda x: transaction['trans_category'] == x.category,
            self._trans_categs)
        if trans_category:
            transaction['trans_category_id'] = trans_category[0].id
            transaction['trans_category_desc'] = trans_category[0].description
        else:
            transaction['trans_category_id'] = None
            transaction['trans_category_desc'] = _(
                "Transaction Category unknown, "
                "please consult your bank.")
        # positions 61-115 : communication
        if line[61] == '1':
            transaction['struct_comm_type'] = line[62:65]
            comm_type = filter(
                lambda x: x.code == transaction['struct_comm_type'],
                self._comm_types)
            if not comm_type:
                err_string = _(
                    "\nThe File contains an invalid "
                    "Structured Communication Type : %s !"
                ) % transaction['struct_comm_type']
                raise UserError(err_string)
            transaction['struct_comm_type_id'] = comm_type[0].id
            transaction['struct_comm_type_desc'] = comm_type[0].description
            transaction['communication'] = transaction['name'] = line[65:115]
            if transaction['struct_comm_type'] in ['101', '102']:
                bbacomm = line[65:77]
                transaction['struct_comm_bba'] = transaction['name'] = \
                    '+++' + bbacomm[0:3] + '/' + bbacomm[3:7] + \
                    '/' + bbacomm[7:] + '+++'
                # SEPA SCT <CdtrRefInf> type
                transaction['creditor_reference_type'] = 'BBA'
                # SEPA SCT <CdtrRefInf> reference
                transaction['creditor_reference'] = bbacomm
        else:
            transaction['communication'] = transaction['name'] = \
                line[62:115].strip()
        transaction['entry_date'] = str2date(line[115:121])
        if transaction['sequence'] == 1:
            coda_statement['first_transaction_date'] = \
                transaction['entry_date']
        # positions 122-124 not processed

        # store transaction
        coda_transactions[transaction_seq] = transaction

        if previous_main_move:

            if previous_main_move.get('detail_cnt') and \
                    previous_main_move.get('promoted'):
                # add closing globalisation level on previous detail record
                # in order to correctly close moves that have been
                # 'promoted' to globalisation
                closeglobalise = coda_transactions[transaction_seq - 1]
                closeglobalise.update({
                    'glob_lvl_flag': previous_main_move['glob_lvl_flag']})
            else:
                # Demote record with globalisation code from
                # 'globalisation' to 'regular' when no detail records.
                # The same logic is repeated on the New Balance Record
                # ('8 Record') in order to cope with CODA files containing
                # a single 2.1 record that needs to be 'demoted'.
                if previous_main_move['type'] == 'globalisation' \
                        and not previous_main_move.get('detail_cnt'):
                    # demote record with globalisation code from
                    # 'globalisation' to 'regular' when no detail records
                    k = previous_main_move['sequence']
                    to_demote = coda_transactions[k]
                    to_demote.update({
                        'type': 'regular',
                        'glob_lvl_flag': 0,
                        'globalisation_amount': False,
                        'amount': previous_main_move['globalisation_amount'],
                    })

            if main_move_stack_pop:
                main_move_stack.pop()

        main_move_stack.append(transaction)
        if glob_lvl_stack_append:
            glob_lvl_stack.append(glob_lvl_flag)
        if glob_lvl_stack_pop:
            glob_lvl_stack.pop()

        return coda_parsing_note, transaction_seq

    def _coda_record_22(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        transaction = coda_statement['coda_transactions'][transaction_seq]
        if transaction['ref'][0:4] != line[2:6]:
            err_string = _(
                "\nCODA parsing error on movement data record 2.2, seq nr %s!"
                "\nPlease report this issue via your Odoo support channel."
            ) % line[2:10]
            raise UserError(err_string)
        comm_extra = line[10:63]
        if not transaction.get('struct_comm_type_id'):
            comm_extra = comm_extra.rstrip()
        transaction['name'] += comm_extra.rstrip()
        transaction['communication'] += comm_extra
        transaction['payment_reference'] = line[63:98].strip()
        transaction['counterparty_bic'] = line[98:109].strip()

        return coda_parsing_note

    def _coda_record_23(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        transaction = coda_statement['coda_transactions'][transaction_seq]
        if transaction['ref'][0:4] != line[2:6]:
            err_string = _(
                "\nCODA parsing error on movement data record 2.3, seq nr %s!"
                "'\nPlease report this issue via your Odoo support channel."
            ) % line[2:10]
            raise UserError(err_string)

        if coda_statement['coda_version'] == '1':
            counterparty_number = line[10:22].strip()
            counterparty_name = line[47:125].strip()
            counterparty_currency = ''
        else:
            if line[22] == ' ':
                counterparty_number = line[10:22].strip()
                counterparty_currency = line[23:26].strip()
            else:
                counterparty_number = line[10:44].strip()
                counterparty_currency = line[44:47].strip()
            counterparty_name = line[47:82].strip()
            comm_extra = line[82:125]
            if not transaction.get('struct_comm_type_id'):
                comm_extra = comm_extra.rstrip()
            transaction['name'] += comm_extra.rstrip()
            transaction['communication'] += comm_extra
        transaction['counterparty_number'] = counterparty_number
        transaction['counterparty_currency'] = counterparty_currency
        transaction['partner_name'] = counterparty_name

        return coda_parsing_note

    def _coda_record_3(self, coda_statement, line, coda_parsing_note,
                       transaction_seq):

        if line[1] == '1':
            coda_parsing_note, transaction_seq = self._coda_record_31(
                coda_statement, line, coda_parsing_note, transaction_seq)

        elif line[1] == '2':
            coda_parsing_note = self._coda_record_32(
                coda_statement, line, coda_parsing_note, transaction_seq)

        elif line[1] == '3':
            coda_parsing_note = self._coda_record_33(
                coda_statement, line, coda_parsing_note, transaction_seq)

        return coda_parsing_note, transaction_seq

    def _coda_record_31(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        # list of lines parsed already
        transaction = coda_statement['coda_transactions'][transaction_seq]

        info_line = {}
        info_line['entry_date'] = transaction['entry_date']
        info_line['type'] = 'information'
        transaction_seq = transaction_seq + 1
        info_line['sequence'] = transaction_seq
        info_line['struct_comm_type'] = ''
        info_line['struct_comm_type_desc'] = ''
        info_line['communication'] = ''
        info_line['ref'] = line[2:10]
        info_line['ref_move'] = line[2:6]
        info_line['ref_move_detail'] = line[6:10]
        info_line['trans_ref'] = line[10:31]
        # get key of associated transaction record
        mm_seq = coda_statement['main_move_stack'][-1]['sequence']
        trans_check = \
            coda_statement['coda_transactions'][mm_seq]['trans_ref']
        if info_line['trans_ref'] != trans_check:
            err_string = _(
                "\nCODA parsing error on "
                "information data record 3.1, seq nr %s !"
                "\nPlease report this issue via your Odoo support channel."
            ) % line[2:10]
            raise UserError(err_string)
        info_line['main_move_sequence'] = mm_seq
        # positions 32-38 : transaction code
        info_line['trans_type'] = line[31]
        trans_type = filter(
            lambda x: x.type == info_line['trans_type'],
            self._trans_types)
        if not trans_type:
            err_string = _(
                "\nThe File contains an invalid CODA Transaction Type : %s !"
            ) % info_line['trans_type']
            raise UserError(err_string)
        info_line['trans_type_desc'] = trans_type[0].description
        info_line['trans_family'] = line[32:34]
        trans_family = filter(
            lambda x: (x.type == 'family') and
            (x.code == info_line['trans_family']),
            self._trans_codes)
        if not trans_family:
            err_string = _(
                "\nThe File contains an invalid CODA Transaction Family : %s !"
            ) % info_line['trans_family']
            raise UserError(err_string)
        trans_family = trans_family[0]
        info_line['trans_family_desc'] = trans_family.description
        info_line['trans_code'] = line[34:36]
        trans_code = filter(
            lambda x: (x.type == 'code') and
            (x.code == info_line['trans_code']) and
            (x.parent_id.id == trans_family.id),
            self._trans_codes)
        if trans_code:
            info_line['trans_code_desc'] = trans_code[0].description
        else:
            info_line['trans_code_desc'] = _(
                "Transaction Code unknown, please consult your bank.")
        info_line['trans_category'] = line[36:39]
        trans_category = filter(
            lambda x: x.category == info_line['trans_category'],
            self._trans_categs)
        if trans_category:
            info_line['trans_category_desc'] = \
                trans_category[0].description
        else:
            info_line['trans_category_desc'] = _(
                "Transaction Category unknown, please consult your bank.")
        # positions 40-113 : communication
        if line[39] == '1':
            info_line['struct_comm_type'] = line[40:43]
            comm_type = filter(
                lambda x: x.code == info_line['struct_comm_type'],
                self._comm_types)
            if not comm_type:
                err_string = _(
                    "\nThe File contains an invalid "
                    "Structured Communication Type : %s !"
                ) % info_line['struct_comm_type']
                raise UserError(err_string)
            info_line['struct_comm_type_desc'] = comm_type[0].description
            info_line['communication'] = line[43:113]
            info_line['name'] = info_line['communication'].strip()
        else:
            name = _("Extra information")
            info = line[40:113]
            info_line['name'] = name + ': ' + info
            info_line['communication'] = INDENT + name + ':'
            info_line['communication'] += INDENT + info
        # positions 114-128 not processed

        # store transaction
        coda_statement['coda_transactions'][transaction_seq] = info_line
        return coda_parsing_note, transaction_seq

    def _coda_record_32(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        transaction = coda_statement['coda_transactions'][transaction_seq]
        if transaction['ref_move'] != line[2:6]:
            err_string = _(
                "\nCODA parsing error on "
                "information data record 3.2, seq nr %s!"
                "\nPlease report this issue via your Odoo support channel."
            ) % transaction['ref']
            raise UserError(err_string)
        comm_extra = line[10:115]
        if not transaction.get('struct_comm_type_id'):
            comm_extra = comm_extra.rstrip()
        transaction['name'] += comm_extra.rstrip()
        transaction['communication'] += comm_extra

        return coda_parsing_note

    def _coda_record_33(self, coda_statement, line, coda_parsing_note,
                        transaction_seq):

        transaction = coda_statement['coda_transactions'][transaction_seq]
        if transaction['ref_move'] != line[2:6]:
            err_string = _(
                "\nCODA parsing error on "
                "information data record 3.3, seq nr %s !"
                "\nPlease report this issue via your Odoo support channel."
            ) % line[2:10]
            raise UserError(err_string)
        comm_extra = line[10:100].rstrip()
        transaction['name'] += comm_extra
        transaction['communication'] += comm_extra

        return coda_parsing_note

    def _coda_record_4(self, coda_statement, line, coda_parsing_note,
                       transaction_seq):

        comm_line = {}
        comm_line['type'] = 'communication'
        transaction_seq = transaction_seq + 1
        comm_line['sequence'] = transaction_seq
        comm_line['ref'] = line[2:10]
        comm_line['communication'] = comm_line['name'] = line[32:112].strip()
        coda_statement['coda_transactions'][transaction_seq] = comm_line

        return coda_parsing_note, transaction_seq

    def _coda_record_8(self, coda_statement, line, coda_parsing_note,
                       transaction_seq):

        cba = coda_statement['coda_bank_params']
        # get list of lines parsed already
        coda_transactions = coda_statement['coda_transactions']

        last_transaction = coda_statement['main_move_stack'][-1]
        if last_transaction['type'] == 'globalisation' \
                and not last_transaction.get('detail_cnt'):
            # demote record with globalisation code from
            # 'globalisation' to 'regular' when no detail records
            main_transaction_seq = last_transaction['sequence']
            to_demote = coda_transactions[main_transaction_seq]
            to_demote.update({
                'type': 'regular',
                'glob_lvl_flag': 0,
                'globalisation_amount': False,
                'amount': last_transaction['globalisation_amount'],
            })
            # add closing globalisation level on previous detail record
            # in order to correctly close moves that have been 'promoted'
            # to globalisation
            if last_transaction.get('detail_cnt') \
                    and last_transaction.get('promoted'):
                closeglobalise = coda_transactions[transaction_seq - 1]
                closeglobalise.update({
                    'glob_lvl_flag': last_transaction['glob_lvl_flag']})
        coda_statement['paper_nb_seq_number'] = line[1:4]
        bal_end = list2float(line[42:57])
        new_balance_date = str2date(line[57:63])
        if not new_balance_date:
            # take date of last transaction
            new_balance_date = last_transaction.get('entry_date')
        coda_statement['new_balance_date'] = new_balance_date
        if line[41] == '1':    # 1=Debit
            bal_end = - bal_end
        coda_statement['balance_end_real'] = bal_end

        # update coda_statement['name'] with data from 8 record
        if cba.coda_st_naming:
            coda_statement['name'] = cba.coda_st_naming % {
                'code': cba.journal_id.code or '',
                'year':
                    coda_statement['new_balance_date'] and
                    coda_statement['new_balance_date'][:4] or
                    coda_statement['date'][:4],
                'y':
                    coda_statement['new_balance_date'] and
                    coda_statement['new_balance_date'][2:4] or
                    coda_statement['date'][2:4],
                'coda': coda_statement['coda_seq_number'],
                'paper_ob': coda_statement['paper_ob_seq_number'],
                'paper': coda_statement['paper_nb_seq_number'],
            }
            # We have to skip the already processed statements
            # when we reprocess CODA file
            if self._coda_id:
                old_statements = self.env['account.bank.statement'].search(
                    [('coda_id', '=', self._coda_id),
                     ('name', '=', coda_statement['name'])])
                if old_statements:
                    coda_statement['skip'] = True
        else:
            coda_statement['name'] = '/'

        return coda_parsing_note

    def _coda_record_9(self, coda_statement, line, coda_parsing_note):

        coda_statement['balance_min'] = list2float(line[22:37])
        coda_statement['balance_plus'] = list2float(line[37:52])
        if not coda_statement.get('balance_end_real'):
            coda_statement['balance_end_real'] = \
                coda_statement['balance_start'] \
                + coda_statement['balance_plus'] \
                - coda_statement['balance_min']
        if coda_parsing_note:
            coda_statement['coda_parsing_note'] = _(
                "'\nStatement Line matching results:"
            ) + coda_parsing_note
        else:
            coda_statement['coda_parsing_note'] = ''

        return coda_parsing_note

    def _check_duplicate(self, coda_statement):
        cba = coda_statement['coda_bank_params']
        discard = False
        if cba.discard_dup:
            dups = self.env['account.bank.statement'].search(
                [('name', '=', coda_statement['name']),
                 ('company_id', '=', cba.company_id.id)])
            if dups:
                # don't create a bank statement for duplicates
                discard = True
                coda_statement['coda_parsing_note'] += _(
                    "\n\nThe Bank Statement %s already exists, "
                    "hence no duplicate Bank Statement has been created."
                ) % coda_statement['name']
        return discard

    def _create_bank_statement(self, coda_statement):

        bank_st = False
        cba = coda_statement['coda_bank_params']
        journal = cba.journal_id
        balance_start_check = False
        balance_start_check_date = coda_statement[
            'first_transaction_date'] or coda_statement['date']
        st_check = self.env['account.bank.statement'].search(
            [('journal_id', '=', journal.id),
             ('date', '<', balance_start_check_date)],
            order='date DESC, id DESC', limit=1)
        if st_check:
            balance_start_check = st_check.balance_end_real
        else:
            account = (
                journal.default_credit_account_id ==
                journal.default_debit_account_id
            ) and journal.default_debit_account_id
            if not account:
                self._nb_err += 1
                self._err_string += _(
                    "'\nConfiguration Error in journal %s!"
                    "\nPlease verify the Default Debit and Credit Account "
                    "settings.") % journal.name
                return bank_st
            else:
                data = self.env['account.move.line'].read_group(
                    [('account_id', '=', account.id),
                     ('date', '<', balance_start_check_date)],
                    ['balance'], [])
                balance_start_check = data and data[0]['balance'] or 0.0

        if balance_start_check != coda_statement['balance_start']:
            balance_start_err_string = _(
                "'\nThe CODA Statement %s Starting Balance (%.2f) "
                "does not correspond with the previous "
                "Closing Balance (%.2f) in journal %s!"
            ) % (coda_statement['name'],
                 coda_statement['balance_start'],
                 balance_start_check, journal.name)
            if cba.balance_start_enforce:
                self._nb_err += 1
                self._err_string += balance_start_err_string
                return bank_st
            else:
                coda_statement[
                    'coda_parsing_note'] += '\n' + balance_start_err_string

        st_vals = {
            'name': coda_statement['name'],
            'journal_id': journal.id,
            'coda_id': self._coda_id,
            'date': self.accounting_date
            or coda_statement['new_balance_date'],
            'balance_start': coda_statement['balance_start'],
            'balance_end_real': coda_statement['balance_end_real'],
            'state': 'open',
            'company_id': cba.company_id.id,
            'coda_bank_account_id': cba.id,
        }

        try:
            with self._cr.savepoint():
                ctx = dict(self._context, force_company=cba.company_id.id)
                st = self.env['account.bank.statement'].with_context(ctx)
                bank_st = st.create(st_vals)
        except (UserError, ValidationError) as e:
            self._nb_err += 1
            self._err_string += _('\nError ! ') + str(e)
            tb = ''.join(format_exception(*exc_info()))
            _logger.error(
                "Application Error while processing Statement %s\n%s",
                coda_statement.get('name', '/'), tb)
        except Exception, e:
            self._nb_err += 1
            self._err_string += _('\nSystem Error : ') + str(e)
            tb = ''.join(format_exception(*exc_info()))
            _logger.error(
                "System Error while processing Statement %s\n%s",
                coda_statement.get('name', '/'), tb)
        except:
            self._nb_err += 1
            self._err_string = _('\nUnknown Error')
            tb = ''.join(format_exception(*exc_info()))
            _logger.error(
                "Unknown Error while processing Statement %s\n%s",
                coda_statement.get('name', '/'), tb)

        return bank_st

    def _prepare_statement_line(self, coda_statement, transaction,
                                coda_parsing_note):

        cba = coda_statement['coda_bank_params']
        ctx = dict(self._context, force_company=cba.company_id.id)

        if not transaction['type'] == 'communication':
            if transaction['trans_family'] in ST_LINE_NAME_FAMILIES:
                transaction['name'] = self._get_st_line_name(transaction)
            if transaction['type'] == 'information':
                if transaction['struct_comm_type'] in PARSE_COMMS_INFO:
                    transaction['name'], transaction['communication'] = \
                        self._parse_comm_info(coda_statement, transaction)
                elif transaction['struct_comm_type'] in PARSE_COMMS_MOVE:
                    transaction['name'], transaction['communication'] = \
                        self._parse_comm_move(coda_statement, transaction)
            elif transaction['struct_comm_type'] in PARSE_COMMS_MOVE:
                    transaction['name'], transaction['communication'] = \
                        self._parse_comm_move(coda_statement, transaction)

        transaction['name'] = transaction['name'].strip()

        # handling transactional records, transaction['type'] in
        # ['globalisation', 'regular']

        if transaction['type'] in ['globalisation', 'regular']:

            if transaction['ref_move_detail'] == '0000':
                # initialise stack with tuples
                # (glob_lvl_flag, glob_code, glob_id, glob_name)
                coda_statement['glob_id_stack'] = [(0, '', 0, '')]

            glob_lvl_flag = transaction['glob_lvl_flag']
            if glob_lvl_flag:
                if coda_statement['glob_id_stack'][-1][0] == glob_lvl_flag:
                    transaction['globalisation_id'] = \
                        coda_statement['glob_id_stack'][-1][2]
                    coda_statement['glob_id_stack'].pop()
                else:
                    glob_name = transaction['name'].strip() or '/'
                    seq_mod = self.env['ir.sequence'].with_context(ctx)
                    glob_code = seq_mod.next_by_code(
                        'statement.line.global')
                    glob_mod = self.env[
                        'account.bank.statement.line.global'
                    ].with_context(ctx)
                    glob_line = glob_mod.create({
                        'code': glob_code,
                        'name': glob_name,
                        'type': 'coda',
                        'parent_id': coda_statement['glob_id_stack'][-1][2],
                        'amount': transaction['globalisation_amount'],
                        'payment_reference': transaction['payment_reference'],
                        'currency_id': cba.currency_id.id,
                    })
                    transaction['globalisation_id'] = glob_line.id
                    coda_statement['glob_id_stack'].append(
                        (glob_lvl_flag, glob_code, glob_line.id, glob_name))

            transaction['note'] = _(
                'Partner Name: %s \nPartner Account Number: %s'
                '\nTransaction Type: %s - %s'
                '\nTransaction Family: %s - %s'
                '\nTransaction Code: %s - %s'
                '\nTransaction Category: %s - %s'
                '\nStructured Communication Type: %s - %s'
                '\nPayment Reference: %s'
                '\nCommunication: %s'
            ) % (transaction['partner_name'],
                 transaction['counterparty_number'],
                 transaction['trans_type'],
                 transaction['trans_type_desc'],
                 transaction['trans_family'],
                 transaction['trans_family_desc'],
                 transaction['trans_code'],
                 transaction['trans_code_desc'],
                 transaction['trans_category'],
                 transaction['trans_category_desc'],
                 transaction['struct_comm_type'],
                 transaction['struct_comm_type_desc'],
                 transaction['payment_reference'],
                 transaction['communication'])

            if glob_lvl_flag == 0:
                transaction['globalisation_id'] = \
                    coda_statement['glob_id_stack'][-1][2]

            transaction['create_bank_st_line'] = True
            if transaction['amount'] != 0.0:
                if not transaction['name']:
                    if transaction['globalisation_id']:
                        transaction['name'] = \
                            coda_statement['glob_id_stack'][-1][3] or ''

        # handling non-transactional records:
        # transaction['type'] in ['information', 'communication']

        elif transaction['type'] == 'information':

            transaction['globalisation_id'] = \
                coda_statement['glob_id_stack'][-1][2]
            transaction['note'] = _(
                'Transaction Type' ': %s - %s'
                '\nTransaction Family: %s - %s'
                '\nTransaction Code: %s - %s'
                '\nTransaction Category: %s - %s'
                '\nStructured Communication Type: %s - %s'
                '\nCommunication: %s'
            ) % (transaction['trans_type'], transaction['trans_type_desc'],
                 transaction['trans_family'], transaction['trans_family_desc'],
                 transaction['trans_code'], transaction['trans_code_desc'],
                 transaction['trans_category'],
                 transaction['trans_category_desc'],
                 transaction['struct_comm_type'],
                 transaction['struct_comm_type_desc'],
                 transaction['communication'])

            # update transaction values generated from the
            # 2.x move record
            mm_seq = transaction['main_move_sequence']
            coda_statement['coda_transactions'][mm_seq]['note'] += \
                '\n' + transaction['communication']

        elif transaction['type'] == 'communication':
            transaction['name'] = 'free communication'
            coda_statement['coda_note'] += \
                '\n' + transaction['communication']

        if not transaction['name']:
            transaction['name'] = ', '.join([
                transaction['trans_family_desc'],
                transaction['trans_code_desc'],
                transaction['trans_category_desc']])
        return coda_parsing_note

    def _get_st_line_move_name(self, coda_statement, transaction):
        move_name = '%s/%s' % (
            coda_statement['name'],
            str(transaction['sequence']).rjust(3, '0'))
        return move_name

    def _prepare_st_line_vals(self, coda_statement, transaction):

        g_seq = transaction.get('glob_sequence')
        if g_seq:
            transaction['upper_transaction'] = \
                coda_statement['coda_transactions'][g_seq]
        move_name = self._get_st_line_move_name(coda_statement, transaction)
        st_line_vals = {
            'sequence': transaction['sequence'],
            'ref': transaction['ref'],
            'name': transaction['name'],
            'val_date': transaction['val_date'],
            'date': transaction['entry_date'],
            'amount': transaction['amount'],
            'partner_name': transaction['partner_name'],
            'counterparty_bic': transaction['counterparty_bic'],
            'counterparty_number': transaction['counterparty_number'],
            'counterparty_currency': transaction['counterparty_currency'],
            'globalisation_id': transaction['globalisation_id'],
            'payment_reference': transaction['payment_reference'],
            'statement_id': coda_statement['bank_st_id'],
            'move_name': move_name,
            'note': transaction['note'],
            'coda_transaction_dict': json.dumps(transaction)}

        if transaction.get('bank_account_id'):
            st_line_vals['bank_account_id'] = transaction['bank_account_id']

        return st_line_vals

    def _create_bank_statement_line(self, coda_statement, transaction):
        st_line_vals = self._prepare_st_line_vals(coda_statement, transaction)
        cba = coda_statement['coda_bank_params']
        ctx = dict(self._context, force_company=cba.company_id.id)
        stl = self.env['account.bank.statement.line'].with_context(ctx)
        st_line = stl.create(st_line_vals)
        transaction['st_line_id'] = st_line.id

    def _discard_empty_statement(self, coda_statement):
        """
        Return False if you do not want to create a bank statement
        for CODA files without transactions.
        """
        coda_statement['coda_parsing_note'] += _(
            "\n\nThe CODA Statement %s does not contain transactions, "
            "hence no Bank Statement has been created."
            "\nSelect the 'CODA Bank Statement' "
            "to check the contents of %s."
        ) % (coda_statement['name'], coda_statement['name'])
        return True

    def _coda_statement_init_hook(self, coda_statement):
        """
        Use this method to take customer specific actions
        once a specific statement has been identified in a coda file.
        """

    def _coda_statement_hook(self, coda_statement):
        """
        Use this method to take customer specific actions
        after the creation of the 'coda_statement' dict by the parsing engine.

        e.g. Do not generate statements without transactions:
        self._normal2info(coda_statement)
        """

    def _coda_transaction_hook(self, coda_statement, transaction):
        """
        Use this method to adapt the transaction created by the
        CODA parsing to customer specific needs.
        """
        transaction_copy = transaction.copy()
        return [transaction_copy]

    @api.multi
    def coda_parsing(self):
        if self.coda_fname.split('.')[-1].lower() == 'zip':
            return self._coda_zip()
        return self._coda_parsing()

    def _coda_zip(self):
        """
        Expand ZIP archive before CODA parsing.
        TODO: refactor code to share logic with 'l10n_be_coda_batch' module
        """
        self._ziplog_note = ''
        self._ziperr_log = ''
        coda_files = []
        try:
            coda_data = base64.decodestring(self.coda_data)
            with zipfile.ZipFile(StringIO(coda_data)) as coda_zip:
                for fn in coda_zip.namelist():
                    if not fn.endswith('/'):
                        coda_files.append((coda_zip.read(fn), fn))
        # fall back to regular CODA file processing if zip expand fails
        except zipfile.BadZipfile, e:
            _logger.error(str(e))
            return self._coda_parsing()
        except:
            tb = ''.join(format_exception(*exc_info()))
            _logger.error("Unknown Error while reading zip file\n%s", tb)
            return self._coda_parsing()
        coda_files = self._sort_files(coda_files)
        coda_ids = []
        bk_st_ids = []

        # process CODA files
        for coda_file in coda_files:
            time_start = time.time()
            try:
                statements = self._coda_parsing(
                    codafile=coda_file[1], codafilename=coda_file[2],
                    batch=True)
                coda_ids += [self._coda_id]
                bk_st_ids += statements.ids
                if self.reconcile:
                    reconcile_note = ''
                    for statement in statements:
                        reconcile_note = self._automatic_reconcile(
                            statement, reconcile_note=reconcile_note)
                    if reconcile_note:
                        self._ziplog_note += reconcile_note
                self._ziplog_note += '\n\n' + _(
                    "CODA File '%s' has been imported.\n"
                ) % coda_file[2]
                self._ziplog_note += (
                    '\n' + _("Number of statements processed")
                    + ' : {}'.format(len(bk_st_ids))
                )
            except UserError, e:
                self._ziperr_log += _(
                    "\n\nError while processing CODA File '%s' :\n%s"
                ) % (coda_file[2], ''.join(e.args))
            except:
                tb = ''.join(format_exception(*exc_info()))
                self._ziperr_log += _(
                    "\n\nError while processing CODA File '%s' :\n%s"
                ) % (coda_file[2], tb)
            file_import_time = time.time() - time_start
            _logger.warn(
                'File %s processing time = %.3f seconds',
                coda_file[2], file_import_time)

        note = _("ZIP archive import results:")
        note += self._ziperr_log + self._ziplog_note
        log_footer = _('\n\nNumber of files : %s') % str(len(coda_files))
        self.note = note + log_footer

        ctx = dict(self.env.context, coda_ids=coda_ids, bk_st_ids=bk_st_ids)
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.account_coda_import_view_form_result' % module)
        return {
            'name': _('CODA ZIP import result'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.coda.import',
            'view_id': result_view.id,
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window',
        }

    def _msg_duplicate(self, filename):
        self._nb_err += 1
        self._ziperr_log += _(
            "\n\nError while processing CODA File '%s' :") % (filename)
        self._ziperr_log += _(
            "\nThis CODA File is marked by your bank as a 'Duplicate' !")
        self._ziperr_log += _(
            '\nPlease treat this CODA File manually !')

    def _msg_exception(self, filename):
        self._nb_err += 1
        self._ziperr_log += _(
            "\n\nError while processing CODA File '%s' :") % (filename)
        self._ziperr_log += _('\nInvalid Header Record !')

    def _msg_noheader(self, filename):
        self._nb_err += 1
        self._ziperr_log += _(
            "\n\nError while processing CODA File '%s' :") % (filename)
        self._ziperr_log += _("\nMissing Header Record !")

    def _sort_files(self, coda_files_in):
        """
        Sort CODA files on creation date.
        """
        coda_files = []
        for data, filename in coda_files_in:
            coda_creation_date = False
            recordlist = unicode(
                data, 'windows-1252', 'strict').split('\n')
            if not recordlist:
                self._nb_err += 1
                self._ziperr_log += _(
                    "\n\nError while processing CODA File '%s' :"
                ) % (filename)
                self._ziperr_log += _("\nEmpty File !")
            else:
                for line in recordlist:
                    if not line:
                        pass
                    elif line[0] == '0':
                        try:
                            coda_creation_date = str2date(line[5:11])
                            if line[16] == 'D':
                                self._msg_duplicate(filename)
                            else:
                                coda_files += [
                                    (coda_creation_date,
                                     data,
                                     filename)]
                        except:
                            self._msg_exception(filename)
                        break
                    else:
                        self._msg_noheader(filename)
                        break
        coda_files.sort()
        return coda_files

    def _coda_parsing(self, codafile=None, codafilename=None,
                      batch=False):
        """
        TODO:
        refactor code to return statements and coda file when called
        in batch mode.
        """
        if batch:
            self._batch = True
            recordlist = unicode(
                codafile, 'windows-1252', 'strict').split('\n')
        else:
            self.ensure_one()
            self._batch = False
            codafile = self.coda_data
            codafilename = self.coda_fname
            recordlist = unicode(
                base64.decodestring(codafile),
                'windows-1252', 'strict').split('\n')

        self._coda_id = self._context.get('coda_id')
        self._coda_banks = self.env['coda.bank.account'].search([])
        self._trans_types = self.env['account.coda.trans.type'].search([])
        self._trans_codes = self.env['account.coda.trans.code'].search([])
        self._trans_categs = self.env[
            'account.coda.trans.category'].search([])
        self._comm_types = self.env['account.coda.comm.type'].search([])
        self._coda_import_note = ''
        coda_statements = []

        # parse lines in coda file and store result in coda_statements list
        coda_statement = {}
        skip = False
        for line in recordlist:

            skip = coda_statement.get('skip')
            if not line:
                continue
            if line[0] != '0' and not coda_statement:
                    raise UserError(_(
                        "CODA Import Failed."
                        "\nIncorrect input file format"))
            elif line[0] == '0':
                # start of a new statement within the CODA file
                coda_statement = {}
                st_line_seq = 0
                coda_parsing_note = ''

                coda_parsing_note = self._coda_record_0(
                    coda_statement, line, coda_parsing_note)

                if not self._coda_id:
                    codas = self.env['account.coda'].search(
                        [('name', '=', codafilename),
                         ('coda_creation_date', '=', coda_statement['date'])])
                    self._coda_id = codas and codas[0].id or False
                    if self._coda_id:
                        self._coda_import_note += '\n\n'
                        self._coda_import_note += _(
                            "CODA File %s has already been imported."
                        ) % codafilename
                        coda_statement['skip'] = True

            elif line[0] == '1':
                coda_parsing_note = self._coda_record_1(
                    coda_statement, line, coda_parsing_note)

            elif line[0] == '2' and not skip:
                # movement data record 2
                coda_parsing_note, st_line_seq = self._coda_record_2(
                    coda_statement, line, coda_parsing_note, st_line_seq)

            elif line[0] == '3' and not skip:
                # information data record 3
                coda_parsing_note, st_line_seq = self._coda_record_3(
                    coda_statement, line, coda_parsing_note, st_line_seq)

            elif line[0] == '4' and not skip:
                # free communication data record 4
                coda_parsing_note, st_line_seq = self._coda_record_4(
                    coda_statement, line, coda_parsing_note, st_line_seq)

            elif line[0] == '8' and not skip:
                # new balance record
                coda_parsing_note = self._coda_record_8(
                    coda_statement, line, coda_parsing_note, st_line_seq)

            elif line[0] == '9':
                # footer record
                coda_parsing_note = self._coda_record_9(
                    coda_statement, line, coda_parsing_note)
                if not coda_statement['skip']:
                    coda_statements.append(coda_statement)

        # end for line in recordlist:

        if not self._coda_id:
            err_string = ''
            try:
                with self._cr.savepoint():
                    if self._batch:
                        codafile = base64.encodestring(codafile)
                    coda = self.env['account.coda'].create({
                        'name': codafilename,
                        'coda_data': codafile,
                        'coda_creation_date': coda_statement['date'],
                        'date': fields.Date.context_today(self),
                        'user_id': self._uid,
                    })
                    self._coda_id = coda.id
            except (UserError, ValidationError) as e:
                err_string = _('\nApplication Error : ') + str(e)
            except Exception, e:
                err_string = _('\nSystem Error : ') + str(e)
            except:
                e = exc_info()[0]
                err_string = _('\nUnknown Error : ') + str(e)
            if err_string:
                raise UserError(_('CODA Import failed !') + err_string)

        self._nb_err = 0
        self._err_string = ''
        bank_statements = self.env['account.bank.statement']

        for coda_statement in coda_statements:

            bank_st = False
            cba = coda_statement['coda_bank_params']
            self._coda_statement_hook(coda_statement)
            discard = self._check_duplicate(coda_statement)
            transactions = coda_statement['coda_transactions']

            if not transactions:
                err_string = _(
                    "\nThe CODA File contains empty CODA Statement %s "
                    "for Bank Account %s !") % (
                        coda_statement['coda_seq_number'],
                        coda_statement['acc_number'] + ' (' +
                        coda_statement['currency'] +
                        ') - ' + coda_statement['description'])
                self._coda_import_note += '\n' + err_string
                discard = self._discard_empty_statement(coda_statement)

            if not discard and not coda_statement.get('skip'):
                bank_st = self._create_bank_statement(coda_statement)
                if bank_st:
                    bank_statements += bank_st
                    coda_statement['bank_st_id'] = bank_st.id
                else:
                    break

            # prepare bank statement line values and merge
            # information records into the statement line
            coda_statement['glob_id_stack'] = []

            coda_parsing_note = coda_statement['coda_parsing_note']

            for x in transactions:
                transaction = transactions[x]
                coda_parsing_note = self._prepare_statement_line(
                    coda_statement, transaction, coda_parsing_note)

            bank_st_transactions = []
            for x in transactions:
                transaction = transactions[x]
                if transaction.get('create_bank_st_line'):
                    res_transaction_hook = self._coda_transaction_hook(
                        coda_statement, transaction)
                    if res_transaction_hook:
                        bank_st_transactions += res_transaction_hook

            # resequence since _coda_transaction_hook may add/remove lines
            transaction_seq = 0
            st_balance_end = round(coda_statement['balance_start'], 2)
            for transaction in bank_st_transactions:
                transaction_seq += 1
                transaction['sequence'] = transaction_seq
                st_balance_end += round(transaction['amount'], 2)
                self._create_bank_statement_line(
                    coda_statement, transaction)

            if round(st_balance_end -
                     coda_statement['balance_end_real'], 2):
                err_string = _(
                    "\nIncorrect ending Balance in CODA Statement %s "
                    "for Bank Account %s !") % (
                        coda_statement['coda_seq_number'],
                        coda_statement['acc_number'] + ' (' +
                        coda_statement['currency'] +
                        ') - ' + coda_statement['description'])
                coda_statement['coda_parsing_note'] += '\n' + err_string

            # trigger calculate balance_end
            bank_st.write(
                {'balance_start': coda_statement['balance_start']})
            journal_name = cba.journal_id.name

            coda_statement['coda_parsing_note'] = coda_parsing_note

            self._coda_import_note = self._coda_import_note + \
                _('\n\nBank Journal: %s'
                  '\nCODA Version: %s'
                  '\nCODA Sequence Number: %s'
                  '\nPaper Statement Sequence Number: %s'
                  '\nBank Account: %s'
                  '\nAccount Holder Name: %s'
                  '\nDate: %s, Starting Balance:  %.2f, Ending Balance: %.2f'
                  '%s'
                  ) % (journal_name,
                       coda_statement['coda_version'],
                       coda_statement['coda_seq_number'],
                       coda_statement.get('paper_nb_seq_number') or
                       coda_statement['paper_ob_seq_number'],
                       coda_statement['acc_number'] +
                       ' (' + coda_statement['currency'] + ') - ' +
                       coda_statement['description'],
                       coda_statement['acc_holder'],
                       coda_statement['date'],
                       float(coda_statement['balance_start']),
                       float(coda_statement['balance_end_real']),
                       coda_statement['coda_parsing_note'] % {
                           'name': coda_statement['name']})

            if coda_statement.get('separate_application') != '00000':
                self._coda_import_note += _(
                    "'\nCode Separate Application: %s"
                ) % coda_statement['separate_application']
            if coda_statement['coda_note']:
                bank_st.write({'coda_note': coda_statement['coda_note']})

        # end 'for coda_statement in coda_statements'

        coda_note_header = '>>> ' + time.strftime('%Y-%m-%d %H:%M:%S') + ' '
        coda_note_header += _("The CODA File has been processed by")
        coda_note_header += " %s :" % self.env.user.name
        coda_note_footer = '\n\n' + _("Number of statements processed") \
            + ' : ' + str(len(coda_statements))

        if not self._nb_err:
            coda = self.env['account.coda'].browse(self._coda_id)
            old_note = coda.note and (coda.note + '\n\n') or ''
            note = coda_note_header + self._coda_import_note \
                + coda_note_footer
            coda.write({'note': old_note + note, 'state': 'done'})
            if self._batch:
                return bank_statements
        else:
            raise UserError(
                _("CODA Import failed !") + self._err_string)

        if self.reconcile:
            reconcile_note = ''
            for st in bank_statements:
                reconcile_note = st._automatic_reconcile(reconcile_note)
            if reconcile_note:
                note += '\n\n'
                note += _("Automatic Reconcile remarks:") + reconcile_note

        self.note = note

        ctx = dict(self.env.context,
                   coda_ids=[self._coda_id],
                   bk_st_ids=bank_statements.ids)
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.account_coda_import_view_form_result' % module)
        return {
            'name': _('Import CODA File result'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.coda.import',
            'view_id': result_view.id,
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window',
        }

    def _automatic_reconcile(self, statement, reconcile_note=None):
        reconcile_note = reconcile_note or ''
        cba = statement.coda_bank_account_id
        if cba:
            self._company_bank_accounts = \
                cba.company_id.bank_journal_ids.mapped(
                    'bank_account_id').mapped('sanitized_acc_number')
            for st_line in statement.line_ids:
                if st_line.amount and not st_line.journal_entry_ids:
                    transaction = st_line.coda_transaction_dict \
                        and json.loads(st_line.coda_transaction_dict)
                    if transaction:
                        try:
                            with self._cr.savepoint():
                                reconcile_note = self._st_line_reconcile(
                                    st_line, cba, transaction, reconcile_note)
                        except:
                            exctype, value = exc_info()[:2]
                            reconcile_note += '\n\n' + _(
                                "Error while processing statement line "
                                "with ref '%s':\n%s, \n%s"
                            ) % (transaction['ref'], str(exctype),
                                 ', '.join(v for v in value if v))
        return reconcile_note

    def _st_line_reconcile(self, st_line, cba, transaction, reconcile_note):

        reconcile_note = self._match_and_reconcile(
            st_line, cba, transaction, reconcile_note)
        if cba.update_partner:
            reconcile_note = self._update_partner_bank(
                st_line, cba, transaction, reconcile_note)

        # override default account mapping by mappings
        # defined in rules engine
        if not transaction.get('counterpart_aml_id') \
                or transaction.get('account_id'):
            if cba.account_mapping_ids:
                kwargs = {
                    'coda_bank_account_id': cba.id,
                    'trans_type_id': transaction['trans_type_id'],
                    'trans_family_id': transaction['trans_family_id'],
                    'trans_code_id': transaction['trans_code_id'],
                    'trans_category_id':
                        transaction['trans_category_id'],
                    'struct_comm_type_id':
                        transaction['struct_comm_type_id'],
                    'partner_id': transaction.get('partner_id'),
                    'freecomm': transaction['communication']
                        if not transaction['struct_comm_type'] else None,
                    'structcomm': transaction['communication']
                        if transaction['struct_comm_type'] else None,
                    'payment_reference': transaction['payment_reference']
                        if transaction['payment_reference'] else None,
                }
                rule = self.env[
                    'coda.account.mapping.rule'].rule_get(**kwargs)
                if rule:
                    for k in rule:
                        transaction[k] = rule[k]

        if transaction.get('counterpart_aml_id') \
                or transaction.get('account_id'):
            reconcile_note = self._create_move_and_reconcile(
                st_line, cba, transaction, reconcile_note)

        if transaction.get('partner_id'):
            st_line.write({'partner_id': transaction['partner_id']})

        return reconcile_note

    def _match_and_reconcile(self, st_line, cba, transaction, reconcile_note):
        """
        Matching and Reconciliation logic.
        Returns: reconcile_note
        """
        # match on payment reference
        reconcile_note, match = self._match_payment_reference(
            st_line, cba, transaction, reconcile_note)
        if match:
            return reconcile_note

        # match on invoice
        reconcile_note, match = self._match_invoice(
            st_line, cba, transaction, reconcile_note)
        if match:
            return reconcile_note

        # match on sale order
        reconcile_note, match = self._match_sale_order(
            st_line, cba, transaction, reconcile_note)
        if match:
            return reconcile_note

        # match on open accounting entries
        reconcile_note, match = self._match_account_move_line(
            st_line, cba, transaction, reconcile_note)
        if match:
            return reconcile_note

        # check if internal_transfer or find partner via counterparty_number
        # when previous lookup steps fail
        reconcile_note, match = self._match_counterparty(
            st_line, cba, transaction, reconcile_note)
        if match:
            return reconcile_note

        return reconcile_note

    def _match_payment_reference(self, st_line, cba, transaction,
                                 reconcile_note):
        """
        placeholder for ISO 20022 Payment Order matching,
        cf. module l10n_be_coda_pain
        """
        return reconcile_note, {}

    def _match_sale_order(self, st_line, cba, transaction, reconcile_note):
        """
        placeholder for sale order matching, cf. module l10n_be_coda_sale
        """
        return reconcile_note, {}

    def _match_invoice_number(self, st_Line, cba, transaction,
                              reconcile_note, free_comm):
        """
        check matching invoice number in free form communication
        combined with matching amount
        """
        inv_ids = False
        amount_fmt = '%.2f'
        if transaction['amount'] > 0:
            amount_rounded = \
                amount_fmt % round(transaction['amount'], 2)
        else:
            amount_rounded = \
                amount_fmt % round(-transaction['amount'], 2)

        select = \
            "SELECT id FROM " \
            "(SELECT id, type, state, amount_total, number, " \
            "reference_type, reference, " \
            "'%s'::text AS free_comm FROM account_invoice " \
            "WHERE state = 'open' AND company_id = %s) sq " \
            "WHERE amount_total = %s" \
            % (free_comm, cba.company_id.id, amount_rounded)

        # 'out_invoice', 'in_refund'
        if transaction['amount'] > 0:
            select2 = " AND type = 'out_invoice' AND " \
                "free_comm ilike '%'||number||'%'"
            self._cr.execute(select + select2)
            res = self._cr.fetchall()
            if res:
                inv_ids = [x[0] for x in res]
            else:
                select2 = " AND type = 'in_refund' AND " \
                    "free_comm ilike '%'||reference||'%'"
                self._cr.execute(select + select2)
                res = self._cr.fetchall()
                if res:
                    inv_ids = [x[0] for x in res]

        # 'in_invoice', 'out_refund'
        else:
            select2 = " AND type = 'in_invoice' AND " \
                "free_comm ilike '%'||reference||'%'"
            self._cr.execute(select + select2)
            res = self._cr.fetchall()
            if res:
                inv_ids = [x[0] for x in res]
            else:
                select2 = " AND type = 'out_refund' AND " \
                    "free_comm ilike '%'||number||'%'"
                self._cr.execute(select + select2)
                res = self._cr.fetchall()
                if res:
                    inv_ids = [x[0] for x in res]

        return inv_ids

    def _match_invoice(self, st_line, cba, transaction, reconcile_note):

        match = {}

        # check bba scor in bank statement line against open invoices
        if transaction['struct_comm_bba'] and cba.find_bbacom:
            if transaction['amount'] > 0:
                dom_customer = [('type', '=', 'out_invoice')]
                dom_supplier = [('type', '=', 'in_refund')]
            else:
                dom_customer = [('type', '=', 'out_refund')]
                dom_supplier = [('type', '=', 'in_invoice')]
            dom_customer += [
                ('state', '=', 'open'),
                ('reference', '=', transaction['struct_comm_bba']),
                ('reference_type', '=', 'bba')]
            dom_supplier += [
                ('state', '=', 'open'),
                ('supplier_payment_ref', '=', transaction['struct_comm_bba']),
                ('supplier_payment_ref_type', '=', 'bba')]
            invoices = self.env['account.invoice'].search(dom_customer)
            if not invoices:
                invoices = self.env['account.invoice'].search(dom_supplier)
            if not invoices:
                reconcile_note += _(
                    "\n    Bank Statement '%s' line '%s':"
                    "\n        There is no invoice matching the "
                    "Structured Communication '%s' !"
                ) % (st_line.statement_id.name, transaction['ref'],
                     transaction['struct_comm_bba'])
            elif len(invoices) == 1:
                match['invoice_id'] = invoices[0].id
            elif len(invoices) > 1:
                reconcile_note += _(
                    "\n    Bank Statement '%s' line '%s':"
                    "\n        There are multiple invoices matching the "
                    "Structured Communication '%s' !"
                    "\n        A manual reconciliation is required."
                ) % (st_line.statement_id.name, transaction['ref'],
                     transaction['struct_comm_bba'])

        # use free comm in bank statement line
        # for lookup against open invoices
        if not match and cba.find_bbacom:
            # extract possible bba scor from free form communication
            # and try to find matching invoice
            free_comm_digits = re.sub(
                '\D', '', transaction['communication'] or '')
            select = \
                "SELECT id FROM " \
                "(SELECT id, type, state, amount_total, number, " \
                "reference_type, reference, " \
                "'%s'::text AS free_comm_digits FROM account_invoice) sq " \
                "WHERE state = 'open' AND reference_type = 'bba' " \
                "AND free_comm_digits LIKE" \
                " '%%'||regexp_replace(reference, '\D', '', 'g')||'%%'" \
                % (free_comm_digits)
            if transaction['amount'] > 0:
                select2 = " AND type IN ('out_invoice', 'in_refund')"
            else:
                select2 = " AND type IN ('in_invoice', 'out_refund')"
            self._cr.execute(select + select2)
            res = self._cr.fetchall()
            if res:
                inv_ids = [x[0] for x in res]
                if len(inv_ids) == 1:
                    match['invoice_id'] = inv_ids[0]

        if not match and transaction['communication'] and cba.find_inv_number:

            # check matching invoice number in free form communication
            free_comm = repl_special(transaction['communication'].strip())
            inv_ids = self._match_invoice_number(
                st_line, cba, transaction, reconcile_note, free_comm)
            if not inv_ids:
                # check matching invoice number in free form communication
                # of upper globalisation level line
                if transaction.get('upper_transaction'):
                    free_comm = repl_special(
                        transaction['upper_transaction']['communication']
                        .strip())
                    inv_ids = self._match_invoice_number(
                        st_line, cba, transaction, reconcile_note, free_comm)

            if inv_ids:
                if len(inv_ids) == 1:
                    match['invoice_id'] = inv_ids[0]
                elif len(inv_ids) > 1:
                    reconcile_note += _(
                        "\n    Bank Statement '%s' line '%s':"
                        "\n        There are multiple invoices matching the "
                        "Invoice Amount and Reference."
                        "\n        A manual reconciliation is required."
                    ) % (st_line.statement_id.name, transaction['ref'])

        if match:
            invoice = self.env['account.invoice'].browse(match['invoice_id'])
            partner = invoice.partner_id.commercial_partner_id
            transaction['partner_id'] = partner.id
            imls = self.env['account.move.line'].search(
                [('move_id', '=', invoice.move_id.id),
                 ('full_reconcile_id', '=', False),
                 ('account_id', '=', invoice.account_id.id)])
            if imls:
                transaction['counterpart_aml_id'] = imls[0].id
            else:
                err_string = _(
                    "\nThe CODA parsing detected a database inconsistency "
                    "while processing movement data record 2.3, seq nr %s !"
                    "'\nPlease report this issue via your "
                    "Odoo support channel."
                ) % transaction['ref']
                err_code = 'M0001'
                if self.batch:
                    return (err_code, err_string)
                raise UserError(err_string)

        return reconcile_note, match

    def _match_aml_other_domain_field(self, st_line, cba, transaction):
        """
        Customise search input data and field.
        """
        search_field = 'ref'
        search_input = repl_special(transaction['communication'].strip())
        return search_field, search_input

    def _match_aml_other_domain(self, st_line, cba, transaction):

        search_field, search_input = self._match_aml_other_domain_field(
            st_line, cba, transaction)
        domain = [(search_field, '=', search_input),
                  ('full_reconcile_id', '=', False),
                  ('account_id.reconcile', '=', True),
                  ('user_type_id.type', 'not in', ['payable', 'receivable'])]
        return domain

    def _match_aml_other(self, st_line, cba, transaction, reconcile_note):
        """
        check matching with non payable/receivable open accounting entries.
        """
        cur = cba.currency_id
        match = {}

        domain = self._match_aml_other_domain(st_line, cba, transaction)
        amls = self.env['account.move.line'].search(domain)

        matches = []
        for aml in amls:
            sign = (aml.debit - aml.credit) > 0 and 1 or -1
            if cur.name == 'EUR':
                amt = sign * aml.amount_residual
                if cur.is_zero(amt - transaction['amount']):
                    matches.append(aml)
            else:
                if aml.currency_id == cur:
                    amt = sign * aml.amount_residual_currency
                    if cur.is_zero(amt - transaction['amount']):
                        matches.append(aml)

        if len(matches) == 1:
            aml = matches[0]
            match['move_line_id'] = aml.id
            transaction['partner_id'] = aml.partner_id.id
            transaction['counterpart_aml_id'] = aml.id

        return reconcile_note, match

    def _match_aml_arap_domain_field(self, st_line, cba, transaction):
        """
        Customise search input data and field.

        The search field is differenct from the one used in the
        standard (manual) bank statement reconciliation.
        By default we search on the 'name' in stead of 'ref' field.

        The ref field is equal to the 'account.move,ref' field. We already
        cover this case in the invoice matching logic (executed before
        falling back to accounting entry matching).
        By a lookup on name, we allow to match on e.g. a set of
        open Payables/Receivables encoded manually or imported from
        an external accounting package
        (hence not generated from an Odoo invoice).
        """
        search_field = 'name'
        search_input = transaction['communication'].strip()
        return search_field, search_input

    def _match_aml_arap_refine(self, st_line, cba, transaction,
                               coda_parsing_note, matches):
        """
        Refine matching logic by parsing the 'search_field'.
        """
        search_field, search_input = self._match_aml_arap_domain_field(
            st_line, cba, transaction)
        refined = []
        for aml in matches:
            aml_lookup_field = getattr(aml, search_field)
            if transaction['struct_comm_bba']:
                aml_lookup_field = re.sub('\D', '', aml_lookup_field)
            if search_input in aml_lookup_field:
                refined.append(aml)
        return refined

    def _match_aml_arap_domain(self, st_line, cba, transaction):
        domain = [('full_reconcile_id', '=', False),
                  ('user_type_id.type', 'in', ['payable', 'receivable']),
                  ('partner_id', '!=', False)]
        return domain

    def _match_aml_arap(self, st_line, cba, transaction, reconcile_note):
        """
        Check match with open payables/receivables.
        This matching logic can be very resource intensive for databases with
        a large number of unreconciled transactions.
        As a consequence this logic is by default disabled when creating a new
        'CODA Bank Account'.
        """
        cur = cba.currency_id
        cpy_cur = cba.company_id.currency_id
        match = {}

        search_field, search_input = self._match_aml_arap_domain_field(
            st_line, cba, transaction)
        if not search_field or not search_input:
            # skip resource intensive mathcing logic
            return reconcile_note, match

        domain = self._match_aml_arap_domain(st_line, cba, transaction)
        amls = self.env['account.move.line'].search(domain)

        matches = []
        for aml in amls:
            sign = (aml.debit - aml.credit) > 0 and 1 or -1
            if cur == cpy_cur:
                amt = sign * aml.amount_residual
                if cur.is_zero(amt - transaction['amount']):
                    matches.append(aml)
            else:
                if aml.currency_id == cur:
                    amt = sign * aml.amount_residual_currency
                    if cur.is_zero(amt - transaction['amount']):
                        matches.append(aml)

        matches = self._match_aml_arap_refine(
            st_line, cba, transaction, reconcile_note, matches)

        if len(matches) == 1:
            aml = matches[0]
            match['move_line_id'] = aml.id
            transaction['partner_id'] = aml.partner_id.id
            transaction['counterpart_aml_id'] = aml.id

        return reconcile_note, match

    def _match_account_move_line(self, st_line, cba, transaction,
                                 reconcile_note):
        """
        Match against open acounting entries.
        """
        match = {}

        if cba.find_account_move_line:

            # exclude non-partner related transactions (e.g. bank costs)
            if not transaction['counterparty_number']:
                return reconcile_note, match

            # match on open receivables/payables
            reconcile_note, match = self._match_aml_arap(
                st_line, cba, transaction, reconcile_note)
            if match:
                return reconcile_note, match

            # match on other open entries
            reconcile_note, match = self._match_aml_other(
                st_line, cba, transaction, reconcile_note)
            if match:
                return reconcile_note, match

        return reconcile_note, match

    def _match_counterparty(self, st_line, cba, transaction, reconcile_note):

        match = {}
        partner_banks = False
        cp_number = transaction['counterparty_number']
        if not cp_number:
            return reconcile_note, match

        transfer_accounts = filter(
            lambda x: cp_number in x,
            self._company_bank_accounts)
        if transfer_accounts:
            # exclude transactions from
            # counterparty_number = bank account number of this statement
            if cp_number not in get_iban_and_bban(
                    cba.bank_id.sanitized_acc_number):
                transaction['account_id'] = cba.transfer_account.id
                match['transfer_account'] = True

        if match or not cba.find_partner:
            return reconcile_note, match

        partner_banks = self.env['res.partner.bank'].search(
            [('sanitized_acc_number', '=', cp_number), '|',
             ('partner_id.company_id', '=', False),
             ('partner_id.company_id', '=', cba.company_id.id)])
        partner_banks = partner_banks.filtered(lambda r: r.partner_id.active)
        if partner_banks:
            # filter out partners that belong to other companies
            # TODO :
            # adapt this logic to cope with
            # res.partner record rule customisations
            partner_banks_2 = []
            for pb in partner_banks:
                add_pb = True
                pb_partner = pb.partner_id
                if not pb_partner.is_company and pb_partner.parent_id:
                    add_pb = False
                try:
                    if pb_partner.company_id and (
                            pb_partner.company_id.id != cba.company_id.id):
                        add_pb = False
                except:
                    add_pb = False
                if add_pb:
                    partner_banks_2.append(pb)
            if len(partner_banks_2) > 1:
                reconcile_note += _(
                    "\n    Bank Statement '%s' line '%s':"
                    "\n        No partner record assigned: "
                    "There are multiple partners with the same "
                    "Bank Account Number '%s'!"
                ) % (st_line.statement_id.name,
                     transaction['ref'], cp_number)
            elif len(partner_banks_2) == 1:
                partner_bank = partner_banks_2[0]
                transaction['bank_account_id'] = partner_bank.id
                transaction['partner_id'] = partner_bank.partner_id.id
                match['partner_id'] = transaction['partner_id']
        else:
            reconcile_note += _(
                "\n    Bank Statement '%s' line '%s':"
                "\n        The bank account '%s' is "
                "not defined for the partner '%s' !"
            ) % (st_line.statement_id.name,
                 transaction['ref'], cp_number,
                 transaction['partner_name'])

        return reconcile_note, match

    def _unlink_duplicate_partner_banks(self, st_line, cba, transaction,
                                        reconcile_note, partner_banks):
        """
        Clean up partner bank duplicates, keep most recently created.
        This logic may conflict with factoring.
        We recommend to receive factoring payments via a separate bank account
        configured without partner bank update.
        """
        partner_bank_dups = partner_banks[:-1]
        partner = partner_banks[0].partner_id
        reconcile_note += _(
            "\n    Bank Statement '%s' line '%s':"
            "\n        Duplicate Bank Account(s) with account number '%s' "
            "for partner '%s' (id:%s) have been removed."
        ) % (st_line.statement_id.name,
             transaction['ref'],
             partner_banks[0].acc_number,
             partner.name,
             partner.id)
        partner_bank_dups.unlink()
        return reconcile_note

    def _update_partner_bank(self, st_line, cba, transaction, reconcile_note):
        """ add bank account to partner record """

        cp = transaction['counterparty_number']
        if transaction.get('partner_id') and cp \
                and transaction.get('account_id') != cba.transfer_account.id:
            partner_banks = self.env['res.partner.bank'].search(
                [('sanitized_acc_number', '=', cp),
                 ('partner_id', '=', transaction['partner_id'])],
                order='id')
            if len(partner_banks) > 1:
                reconcile_note = self._unlink_duplicate_partner_banks(
                    st_line, cba, transaction, reconcile_note, partner_banks)

            if not partner_banks:
                feedback = self.update_partner_bank(
                    transaction['counterparty_bic'],
                    transaction['counterparty_number'],
                    transaction['partner_id'], transaction['partner_name'])
                if feedback:
                    reconcile_note += _(
                        "\n    Bank Statement '%s' line '%s':"
                    ) % (st_line.statement_id.name, transaction['ref']
                         ) + feedback

        return reconcile_note

    def _prepare_new_aml_dict(self, st_line, cba, transaction):

        new_aml_dict = {
            'account_id': transaction['account_id'],
            'name': transaction['name'],
        }
        if transaction.get('account_tax_id'):
            if transaction['tax_type'] == 'base':
                new_aml_dict['tax_ids'] = [transaction['account_tax_id']]
            else:
                new_aml_dict['tax_line_id'] = transaction['account_tax_id']
        if transaction.get('analytic_account_id'):
            new_aml_dict['analytic_account_id'] = \
                transaction['analytic_account_id']
        # the process_reconciliation method takes assumes that the
        # input mv_line_dict 'debit'/'credit' contains the amount
        # in bank statement line currency and will handle the currency
        # conversions
        if transaction['amount'] > 0:
            new_aml_dict['debit'] = 0.0
            new_aml_dict['credit'] = transaction['amount']
        else:
            new_aml_dict['debit'] = -transaction['amount']
            new_aml_dict['credit'] = 0.0

        return new_aml_dict

    def _prepare_counterpart_aml_dict(self, st_line, cba, transaction):

        aml = self.env['account.move.line'].browse(
            transaction['counterpart_aml_id'])
        am_name = aml.move_id.name if aml.move_id.name != '/' else ''
        aml_name = aml.name
        name = ' '.join([am_name, aml_name])
        counterpart_aml_dict = {
            'move_line': aml,
            'name': name,
        }
        # the process_reconciliation method takes assumes that the
        # input mv_line_dict 'debit'/'credit' contains the amount
        # in bank statement line currency and will handle the currency
        # conversions
        if transaction['amount'] > 0:
            counterpart_aml_dict['debit'] = 0.0
            counterpart_aml_dict['credit'] = transaction['amount']
        else:
            counterpart_aml_dict['debit'] = -transaction['amount']
            counterpart_aml_dict['credit'] = 0.0

        return counterpart_aml_dict

    def _create_move_and_reconcile(self, st_line, cba, transaction,
                                   reconcile_note):

        counterpart_aml_dicts = payment_aml_rec = new_aml_dicts = None
        if transaction.get('counterpart_aml_id'):
            counterpart_aml_dict = self._prepare_counterpart_aml_dict(
                st_line, cba, transaction)
            counterpart_aml_dicts = [counterpart_aml_dict]
        if transaction.get('account_id'):
            new_aml_dict = self._prepare_new_aml_dict(
                st_line, cba, transaction)
            new_aml_dicts = [new_aml_dict]
        if counterpart_aml_dicts or payment_aml_rec or new_aml_dicts:
            err = '\n\n' + _(
                "Error while processing statement line "
                "with ref '%s':"
            ) % transaction['ref']
            try:
                with self._cr.savepoint():
                    st_line.process_reconciliation(
                        counterpart_aml_dicts=counterpart_aml_dicts,
                        payment_aml_rec=payment_aml_rec,
                        new_aml_dicts=new_aml_dicts)
            except (UserError, ValidationError) as e:
                name, value = e[:2]
                reconcile_note += err + _('\nApplication Error : ') + name
                if value:
                    reconcile_note += ', ' + value
            except Exception, e:
                reconcile_note += err + _('\nSystem Error : ') + str(e)
            except:
                exctype, value = exc_info()[:2]
                reconcile_note += err + _(
                    '\nUnknown Error : ') + str(exctype) + ', ' + str(value)
        return reconcile_note

    @api.multi
    def action_open_bank_statements(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id(
            'account', 'action_bank_statement_tree')
        domain = eval(action.get('domain') or '[]')
        domain += [('coda_id', 'in', self.env.context.get('coda_ids'))]
        action.update({'domain': domain})
        return action

    @api.multi
    def action_open_coda_files(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id(
            'l10n_be_coda_advanced', 'account_coda_action')
        domain = eval(action.get('domain') or '[]')
        domain += [('id', 'in', self.env.context.get('coda_ids'))]
        action.update({'domain': domain})
        return action

    @api.multi
    def button_close(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def _get_st_line_name(self, transaction):
        st_line_name = transaction['name']

        if transaction['trans_family'] == '35' \
                and transaction['trans_code'] in ['01', '37']:
            st_line_name = ', '.join(
                [_('Closing'),
                 transaction['trans_code_desc'],
                 transaction['trans_category_desc']])

        if transaction['trans_family'] in ['13', '41']:
            st_line_name = ', '.join(
                [transaction['trans_family_desc'],
                 transaction['trans_code_desc'],
                 transaction['trans_category_desc']])

        if transaction['trans_family'] in ['80']:
            st_line_name = ', '.join(
                [transaction['trans_code_desc'],
                 transaction['trans_category_desc']])

        return st_line_name

    def get_bank(self, bic, iban):

        feedback = False
        country_code = iban[:2]
        bank = self.env['res.bank']
        country = self.env['res.country'].search(
            [('code', '=', country_code)])
        if not country:
            feedback = _(
                "\n        Bank lookup failed due to missing Country "
                "definition for Country Code '%s' !"
            ) % (country_code)
        else:
            bank_country = country[0]
            if iban[:2] == 'BE':
                # To DO : extend for other countries
                bank_code = iban[4:7]
                if bic:
                    banks = self.env['res.bank'].search(
                        [('bic', '=', bic),
                         ('code', '=', bank_code),
                         ('country', '=', bank_country.id)])
                    if banks:
                        bank = banks[0]
                    else:
                        bank = self.env['res.bank'].create({
                            'name': bic,
                            'code': bank_code,
                            'bic': bic,
                            'country': bank_country.id,
                        })
                else:
                    banks = self.env['res.bank'].search(
                        [('code', '=', bank_code),
                         ('country', '=', bank_country.id)])
                    if banks:
                        bank = banks[0]
                        bic = bank.bic
                    else:
                        feedback = _(
                            "\n        Bank lookup failed. "
                            "Please define a Bank with "
                            "Code '%s' and Country '%s' !"
                        ) % (bank_code, bank_country.name)
            else:
                if not bic:
                    feedback = _(
                        "\n        Bank lookup failed due to missing BIC "
                        "in Bank Statement for IBAN '%s' !"
                    ) % (iban)
                else:
                    banks = self.env['res.bank'].search(
                        [('bic', '=', bic),
                         ('country', '=', bank_country.id)])
                    if not banks:
                        bank_name = bic
                        bank = self.env['res.bank'].create({
                            'name': bank_name,
                            'bic': bic,
                            'country': bank_country.id,
                        })
                    else:
                        bank = banks[0]

        bank_id = bank and bank.id or False
        bank_name = bank and bank.name or False
        return bank_id, bic, bank_name, feedback

    def update_partner_bank(self, bic, iban, partner_id, partner_name):

        bank_id = False
        feedback = False
        if check_iban(iban):
            bank_id, bic, bank_name, feedback = self.get_bank(bic, iban)
            if not bank_id:
                return feedback
        else:
            # convert belgian BBAN numbers to IBAN
            if check_bban('BE', iban):
                kk = calc_iban_checksum('BE', iban)
                iban = 'BE' + kk + iban
                bank_id, bic, bank_name, feedback = self.get_bank(bic, iban)
                if not bank_id:
                    return feedback

        if bank_id:
            self.env['res.partner.bank'].create({
                'partner_id': partner_id,
                'bank_id': bank_id,
                'acc_type': 'iban',
                'acc_number': iban,
            })
        return feedback

    def _parse_comm_move(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        method_name = '_parse_comm_move_' + comm_type
        if method_name in dir(self):
            method_instance = getattr(self, method_name)
            st_line_name, st_line_comm = method_instance(
                coda_statement, transaction)
        else:  # To DO : '121', '122', '126'
            _logger.warn(
                "The parsing of Structured Commmunication Type %s "
                "has not yet been implemented. "
                "Please contact Noviat (info@noviat.com) for more information"
                " about the development roadmap", comm_type)
            st_line_name = transaction['name']
            st_line_comm = transaction['communication']
        return st_line_name, st_line_comm

    def _parse_comm_move_100(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = _(
            "Payment with ISO 11649 structured format communication")
        st_line_comm = '\n' + INDENT + _(
            "Payment with a structured format communication "
            "applying the ISO standard 11649"
        ) + ':'
        st_line_comm += INDENT + _(
            "Structured creditor reference to remittance information")
        st_line_comm += INDENT + comm
        return st_line_name, st_line_comm

    def _parse_comm_move_101(self, coda_statement, transaction):
        comm = st_line_comm = transaction['communication']
        st_line_name = st_line_comm = \
            '+++' + comm[0:3] + '/' + comm[3:7] + '/' + comm[7:12] + '+++'
        return st_line_name, st_line_comm

    def _parse_comm_move_102(self, coda_statement, transaction):
        comm = st_line_comm = transaction['communication']
        st_line_name = st_line_comm = \
            '+++' + comm[0:3] + '/' + comm[3:7] + '/' + comm[7:12] + '+++'
        return st_line_name, st_line_comm

    def _parse_comm_move_103(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = ', '.join(
            [transaction['trans_family_desc'], _('Number')])
        st_line_comm = comm
        return st_line_name, st_line_comm

    def _parse_comm_move_105(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = st_line_comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type, self._comm_types)[0].description
        amount = transaction.get('amount', 0.0)
        sign = amount < 0 and -1 or 1
        amount_currency_account = sign * list2float(comm[0:15])
        amount_currency_original = sign * list2float(comm[15:30])
        rate = number2float(comm[30:42], 8)
        currency = comm[42:45].strip()
        struct_format_comm = comm[45:57].strip()
        country_code = comm[57:59].strip()
        amount_eur = sign * list2float(comm[59:74])
        st_line_comm = '\n' + INDENT + st_line_name + INDENT + _(
            "Gross amount in the currency of the account"
        ) + ': %.2f' % amount_currency_account
        if amount_currency_original:
            st_line_comm += INDENT + _(
                "Gross amount in the original currency"
            ) + ': %.2f' % amount_currency_original
        if rate:
            st_line_comm += INDENT + _('Rate') + ': %.4f' % rate
        if currency:
            st_line_comm += INDENT + _('Currency') + ': %s' % currency
        if struct_format_comm:
            st_line_comm += INDENT + _('Structured format communication') \
                + ': %s' % struct_format_comm
        if country_code:
            st_line_comm += INDENT + _('Country code of the principal') \
                + ': %s' % country_code
        if amount_eur:
            st_line_comm += INDENT + _('Equivalent in EUR') \
                + ': %.2f' % amount_eur
        st_line_comm += '\n'
        return st_line_name, st_line_comm

    def _parse_comm_move_106(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = _(
            "VAT, withholding tax on income, commission, etc.")
        st_line_comm = '\n' + INDENT + st_line_name + INDENT + _(
            "Equivalent in the currency of the account"
        ) + ': %.2f' % list2float(comm[0:15])
        st_line_comm += INDENT + _('Amount on which % is calculated') \
            + ': %.2f' % list2float(comm[15:30])
        st_line_comm += INDENT + _('Percent') \
            + ': %.4f' % number2float(comm[30:42], 8)
        st_line_comm += INDENT + (
            comm[42] == 1 and
            _('Minimum applicable') or
            _('Minimum not applicable')
        )
        st_line_comm += INDENT + _('Equivalent in EUR') \
            + ': %.2f' % list2float(comm[43:58])
        return st_line_name, st_line_comm

    def _parse_comm_move_107(self, coda_statement, transaction):
        comm = transaction['communication']
        paid_refusals = {
            '0': _('paid'),
            '1': _('direct debit cancelled or nonexistent'),
            '2': _('refusal - other reason'),
            'D': _('payer disagrees'),
            'E': _('direct debit number linked to another '
                   'identification number of the creditor')}
        st_line_name = _('Direct debit - DOM\'80')
        direct_debit_number = comm[0:12].strip()
        pivot_date = str2date(comm[12:18])
        comm_zone = comm[18:48]
        paid_refusal = paid_refusals.get(comm[48], '')
        creditor_number = comm[49:60].strip()
        st_line_comm = '\n' + INDENT + st_line_name + INDENT + _(
            'Direct Debit Number') + ': %s' % direct_debit_number
        st_line_comm += INDENT + _('Central (Pivot) Date') \
            + ': %s' % pivot_date
        st_line_comm += INDENT + _('Communication Zone') \
            + ': %s' % comm_zone
        st_line_comm += INDENT + _('Paid or reason for refusal') \
            + ': %s' % paid_refusal
        st_line_comm += INDENT + _("Creditor's Number") \
            + ': %s' % creditor_number
        return st_line_name, st_line_comm

    def _parse_comm_move_108(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = _(
            'Closing, period from %s to %s'
        ) % (str2date(comm[42:48]), str2date(comm[48:54]))
        interest = comm[30:42].strip('0')
        st_line_comm = '\n' + INDENT + st_line_name + INDENT + _(
            'Equivalent in the currency of the account'
        ) + ': %.2f' % list2float(comm[0:15])
        if interest:
            st_line_comm += INDENT + _(
                'Interest rates, calculation basis'
            ) + ': %.2f' % list2float(comm[15:30]) + INDENT + _(
                'Interest'
            ) + ': %.2f' % list2float(comm[30:42])
        return st_line_name, st_line_comm

    def _parse_comm_move_111(self, coda_statement, transaction):
        comm = transaction['communication']
        card_schemes = {
            '1': 'Bancontact/Mister Cash',
            '2': _('Private'),
            '3': 'Maestro',
            '5': 'TINA',
            '9': _('Other')}
        trans_types = {
            '0': _('Cumulative'),
            '1': _('Withdrawal'),
            '2': _('Cumulative on network'),
            '5': _('POS others'),
            '7': _('Distribution sector'),
            '8': _('Teledata'),
            '9': _('Fuel')}
        st_line_name = _('POS credit - globalisation')
        card_scheme = card_schemes.get(comm[0], '')
        pos_number = comm[1:7].strip()
        period_number = comm[7:10].strip()
        first_sequence_number = comm[10:16].strip()
        trans_first_date = str2date(comm[16:22])
        last_sequence_number = comm[22:28].strip()
        trans_last_date = str2date(comm[28:34])
        trans_type = trans_types.get(comm[34], '')
        terminal_name = comm[35:50].strip()
        terminal_city = comm[51:60].strip()
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Card Scheme') + ': %s' % card_scheme
        st_line_comm += INDENT + _('POS Number') + ': %s' % pos_number
        st_line_comm += INDENT + _('Period Number') \
            + ': %s' % period_number
        st_line_comm += INDENT + _('First Transaction Sequence Number') \
            + ': %s' % first_sequence_number
        st_line_comm += INDENT + _('Date of first transaction') \
            + ': %s' % trans_first_date
        st_line_comm += INDENT + _('Last Transaction Sequence Number') \
            + ': %s' % last_sequence_number
        st_line_comm += INDENT + _('Date of last transaction') \
            + ': %s' % trans_last_date
        st_line_comm += INDENT + _('Transaction Type') \
            + ': %s' % trans_type
        st_line_comm += INDENT + _('Terminal Identification') + \
            ': %s' % terminal_name + ', ' + terminal_city
        return st_line_name, st_line_comm

    def _parse_comm_move_113(self, coda_statement, transaction):
        comm = transaction['communication']
        card_schemes = {
            '1': 'Bancontact/Mister Cash',
            '2': 'Maestro',
            '3': _('Private'),
            '9': _('Other')}
        trans_types = {
            '1': _('Withdrawal'),
            '2': _('Proton loading'),
            '3': _('Reimbursement Proton balance'),
            '4': _('Reversal of purchases'),
            '5': _('POS others'),
            '7': _('Distribution sector'),
            '8': _('Teledata'),
            '9': _('Fuel')}
        product_codes = {
            '01': _('premium with lead substitute'),
            '02': _('europremium'),
            '03': _('diesel'),
            '04': _('LPG'),
            '06': _('premium plus 98 oct'),
            '07': _('regular unleaded'),
            '08': _('domestic fuel oil'),
            '09': _('lubricants'),
            '10': _('petrol'),
            '11': _('premium 99+'),
            '12': _('Avgas'),
            '16': _('other types'),
        }
        st_line_name = _('ATM/POS debit')
        card_number = comm[0:16].strip()
        card_scheme = card_schemes.get(comm[16], '')
        terminal_number = comm[17:23].strip()
        sequence_number = comm[23:29].strip()
        trans_date = comm[29:35].strip() and str2date(comm[29:35]) or ''
        trans_hour = comm[35:39].strip() and str2time(comm[35:39]) or ''
        trans_type = trans_types.get(comm[39], '')
        terminal_name = comm[40:56].strip()
        terminal_city = comm[56:66].strip()
        orig_amount = comm[66:81].strip() and list2float(comm[66:81])
        rate = number2float(comm[81:93], 8)
        currency = comm[93:96]
        volume = number2float(comm[96:101], 2)
        product_code = product_codes.get(comm[101:103], '')
        unit_price = number2float(comm[103:108], 2)
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Card Number') + ': %s' % card_number
        st_line_comm += INDENT + _('Card Scheme') + ': %s' % card_scheme
        if terminal_number:
            st_line_comm += INDENT + _('Terminal Number') \
                + ': %s' % terminal_number
        st_line_comm += INDENT + _('Transaction Sequence Number') \
            + ': %s' % sequence_number
        st_line_comm += INDENT + _('Time') \
            + ': %s' % trans_date + ' ' + trans_hour
        st_line_comm += INDENT + _('Transaction Type') \
            + ': %s' % trans_type
        st_line_comm += INDENT + _('Terminal Identification') \
            + ': %s' % terminal_name + ', ' + terminal_city
        if orig_amount:
            st_line_comm += INDENT + _('Original Amount') \
                + ': %.2f' % orig_amount
            st_line_comm += INDENT + _('Rate') + ': %.4f' % rate
            st_line_comm += INDENT + _('Currency') + ': %s' % currency
        if volume:
            st_line_comm += INDENT + _('Volume') + ': %.2f' % volume
        if product_code:
            st_line_comm += INDENT + _('Product Code') \
                + ': %s' % product_code
        if unit_price:
            st_line_comm += INDENT + _('Unit Price') \
                + ': %.2f' % unit_price
        return st_line_name, st_line_comm

    def _parse_comm_move_114(self, coda_statement, transaction):
        comm = transaction['communication']
        card_schemes = {
            '1': 'Bancontact/Mister Cash',
            '2': 'Maestro',
            '3': _('Private'),
            '5': 'TINA',
            '9': _('Other')}
        trans_types = {
            '1': _('Withdrawal'),
            '5': _('POS others'),
            '7': _('Distribution sector'),
            '8': _('Teledata'),
            '9': _('Fuel')}
        st_line_name = _('POS credit - individual transaction')
        card_scheme = card_schemes.get(comm[0], '')
        pos_number = comm[1:7].strip()
        period_number = comm[7:10].strip()
        sequence_number = comm[10:16].strip()
        trans_date = str2date(comm[16:22])
        trans_hour = str2time(comm[22:26])
        trans_type = trans_types.get(comm[26], '')
        terminal_name = comm[27:43].strip()
        terminal_city = comm[43:53].strip()
        trans_reference = comm[53:69].strip()
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Card Scheme') + ': %s' % card_scheme
        if pos_number:
            st_line_comm += INDENT + _('POS Number') + ': %s' % pos_number
        if period_number:
            st_line_comm += INDENT + _('Period Number') \
                + ': %s' % period_number
        if sequence_number:
            st_line_comm += INDENT + _('Transaction Sequence Number') \
                + ': %s' % sequence_number
        if trans_date or trans_hour:
            st_line_comm += INDENT + _('Time') \
                + ': %s' % trans_date + ' ' + trans_hour
        if trans_type:
            st_line_comm += INDENT + _('Transaction Type') \
                + ': %s' % trans_type
        if terminal_name or terminal_city:
            st_line_comm += INDENT + _('Terminal Identification') \
                + ': %s' % terminal_name + ', ' + terminal_city
        if trans_reference:
            st_line_comm += INDENT + _('Transaction Reference') \
                + ': %s' % trans_reference
        return st_line_name, st_line_comm

    def _parse_comm_move_115(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = _('Terminal cash deposit')
        card_schemes = {
            '2': _('Private'),
            '9': _('Other')}
        card_number = comm[:16].strip()
        card_scheme = card_schemes.get(comm[16], '')
        terminal_number = comm[17:23].strip()
        sequence_number = comm[23:29].strip()
        payment_day = comm[29:35].strip()
        payment_hour = comm[35:39].strip()
        validation_date = comm[39:45].strip()
        validation_sequence_number = comm[45:51].strip()
        amount = list2float(comm[51:66])
        conformity_code = comm[66].strip()
        terminal_name = comm[67:83].strip()
        terminal_city = comm[83:93].strip()
        message = comm[93:105].strip()
        td = {}
        st_line_comm = '\n' + INDENT + st_line_name
        if card_number:
            td['card_number'] = card_number
            st_line_comm += INDENT + _('Card Number') + ': %s' % card_number
        if card_scheme:
            td['card_scheme'] = card_scheme
            st_line_comm += INDENT + _('Card Scheme') + ': %s' % card_scheme
        if terminal_number:
            td['terminal_number'] = terminal_number
            st_line_comm += INDENT + _('Terminal Number') \
                + ': %s' % terminal_number
        if sequence_number:
            td['sequence_number'] = sequence_number
            st_line_comm += INDENT + _('Transaction Sequence Number') \
                + ': %s' % sequence_number
        if payment_day or payment_hour:
            td['payment_day'] = payment_day
            td['payment_hour'] = payment_hour
            st_line_comm += INDENT + _('Time') \
                + ': %s' % payment_day + ' ' + payment_hour
        if validation_date:
            td['validation_date'] = validation_date
            st_line_comm += INDENT + _('Validation Date') \
                + ': %s' % validation_date
        if validation_sequence_number:
            td['validation_sequence_number'] = validation_sequence_number
            st_line_comm += INDENT + _('Validation Sequence Number') \
                + ': %s' % validation_sequence_number
        td['amount'] = amount
        st_line_comm += INDENT + _('Amount (given by the customer)') \
            + ': %.2f' % amount
        if conformity_code:
            td['conformity_code'] = conformity_code
            st_line_comm += INDENT + _('Conformity Code') \
                + ': %s' % conformity_code
        if terminal_name or terminal_city:
            td['terminal_name'] = terminal_name
            td['terminal_city'] = terminal_city
            st_line_comm += INDENT + _('Terminal Identification') \
                + ': %s' % terminal_name + ', ' + terminal_city
        if message:
            td['message'] = message
            st_line_comm += INDENT + _('Message') + ': %s' % message
        transaction['struct_comm_115'] = td
        return st_line_name, st_line_comm

    def _parse_comm_move_123(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = transaction['name']
        starting_date = str2date(comm[0:6])
        maturity_date = comm[6:12] == '999999' \
            and _('guarantee without fixed term') or str2date(comm[0:6])
        basic_amount = list2float(comm[12:27])
        percent = number2float(comm[27:39], 8)
        term = comm[39:43].lstrip('0')
        minimum = comm[43] == '1' and True or False
        guarantee_number = comm[44:57].strip()
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Starting Date') + ': %s' % starting_date
        st_line_comm += INDENT + _('Maturity Date') \
            + ': %s' % maturity_date
        st_line_comm += INDENT + _('Basic Amount') \
            + ': %.2f' % basic_amount
        st_line_comm += INDENT + _('Percentage') + ': %.4f' % percent
        st_line_comm += INDENT + _('Term in days') + ': %s' % term
        st_line_comm += INDENT + (
            minimum and _('Minimum applicable') or
            _('Minimum not applicable'))
        st_line_comm += INDENT + _(
            'Guarantee Number') + ': %s' % guarantee_number
        return st_line_name, st_line_comm

    def _parse_comm_move_124(self, coda_statement, transaction):
        comm = transaction['communication']
        card_issuers = {
            '1': 'Mastercard',
            '2': 'Visa',
            '3': 'American Express',
            '4': 'Diners Club',
            '9': _('Other')}
        st_line_name = _('Settlement credit cards')
        card_number = comm[0:20].strip()
        card_issuer = card_issuers.get(comm[20], '')
        invoice_number = comm[21:33].strip()
        identification_number = comm[33:48].strip()
        date = comm[48:54].strip() and str2date(comm[48:54]) or ''
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Card Number') + ': %s' % card_number
        st_line_comm += INDENT + _('Issuing Institution') \
            + ': %s' % card_issuer
        st_line_comm += INDENT + _('Invoice Number') \
            + ': %s' % invoice_number
        st_line_comm += INDENT + _('Identification Number') \
            + ': %s' % identification_number
        st_line_comm += INDENT + _('Date') + ': %s' % date
        return st_line_name, st_line_comm

    def _parse_comm_move_125(self, coda_statement, transaction):
        comm = transaction['communication']
        st_line_name = transaction['name']
        if transaction['trans_family'] not in ST_LINE_NAME_FAMILIES:
            st_line_name = _('Credit')
        credit_account = comm[0:27].strip()
        if check_bban('BE', credit_account):
            credit_account = '-'.join(
                [credit_account[:3],
                 credit_account[3:10],
                 credit_account[10:]])
        old_balance = list2float(comm[27:42])
        new_balance = list2float(comm[42:57])
        amount = list2float(comm[57:72])
        currency = comm[72:75]
        start_date = str2date(comm[75:81])
        end_date = str2date(comm[81:87])
        rate = number2float(comm[87:99], 8)
        trans_reference = comm[99:112].strip()
        st_line_comm = '\n' + INDENT + st_line_name + INDENT \
            + _('Credit Account Number') + ': %s' % credit_account
        st_line_comm += INDENT + _('Old Balance') + ': %.2f' % old_balance
        st_line_comm += INDENT + _('New Balance') + ': %.2f' % new_balance
        st_line_comm += INDENT + _('Amount') + ': %.2f' % amount
        st_line_comm += INDENT + _('Currency') + ': %s' % currency
        st_line_comm += INDENT + _('Starting Date') + ': %s' % start_date
        st_line_comm += INDENT + _('End Date') + ': %s' % end_date
        st_line_comm += INDENT + _(
            'Nominal Interest Rate or Rate of Charge') + ': %.4f' % rate
        st_line_comm += INDENT + _(
            'Transaction Reference') + ': %s' % trans_reference
        return st_line_name, st_line_comm

    def _parse_comm_move_127(self, coda_statement, transaction):
        comm = transaction['communication']
        direct_debit_types = {
            '0': _('unspecified'),
            '1': _('recurrent'),
            '2': _('one-off'),
            '3': _('1-st (recurrent)'),
            '4': _('last (recurrent)')}
        direct_debit_schemes = {
            '0': _('unspecified'),
            '1': _('SEPA core'),
            '2': _('SEPA B2B')}
        paid_refusals = {
            '0': _('paid'),
            '1': _('technical problem'),
            '2': _('refusal - reason not specified'),
            '3': _('debtor disagrees'),
            '4': _('debtor\'s account problem')}
        R_types = {
            '0': _('paid'),
            '1': _('reject'),
            '2': _('return'),
            '3': _('refund'),
            '4': _('reversal'),
            '5': _('cancellation')}
        st_line_name = _('European direct debit (SEPA)')
        settlement_date = str2date(comm[0:6])
        direct_debit_type = direct_debit_types.get(comm[6])
        direct_debit_scheme = direct_debit_schemes.get(comm[7])
        paid_refusal = paid_refusals.get(comm[8])
        creditor_id = comm[9:44].strip()
        mandate_ref = comm[44:79].strip()
        comm_zone = comm[79:141].strip()
        R_type = R_types.get(comm[141])
        reason = comm[142:146].strip()
        td = {}
        st_line_comm = '\n' + INDENT + st_line_name
        if settlement_date:
            td['settlement_date'] = settlement_date
            st_line_comm += INDENT + _('Settlement Date') \
                + ': %s' % settlement_date
        if direct_debit_type:
            td['direct_debit_type'] = direct_debit_type
            st_line_comm += INDENT + _('Direct Debit Type') \
                + ': %s' % direct_debit_type
        if direct_debit_scheme:
            td['direct_debit_scheme'] = direct_debit_scheme
            st_line_comm += INDENT + _('Direct Debit Scheme') \
                + ': %s' % direct_debit_scheme
        if paid_refusal:
            td['paid_refusal'] = paid_refusal
            st_line_comm += INDENT + _('Paid or reason for refusal') \
                + ': %s' % paid_refusal
        if creditor_id:
            td['creditor_id'] = creditor_id
            st_line_comm += INDENT + _('Creditor\'s Identification Code') \
                + ': %s' % creditor_id
        if mandate_ref:
            td['mandate_ref'] = mandate_ref
            st_line_comm += INDENT + _('Mandate Reference') \
                + ': %s' % mandate_ref
        if comm_zone:
            td['comm_zone'] = comm_zone
            st_line_comm += INDENT + _('Communication') + ': %s' % comm_zone
        if R_type:
            td['R_type'] = R_type
            st_line_comm += INDENT + _('R transaction Type') + ': %s' % R_type
        if reason:
            td['reason'] = reason
            st_line_comm += INDENT + _('Reason') + ': %s' % reason
        transaction['struct_comm_127'] = td
        return st_line_name, st_line_comm

    def _parse_comm_info(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        method_name = '_parse_comm_info_' + comm_type
        if method_name in dir(self):
            method_instance = getattr(self, method_name)
            st_line_name, st_line_comm = method_instance(
                coda_statement, transaction)
        else:  # To DO : 010, 011
            _logger.warn(
                "The parsing of Structured Commmunication Type %s "
                "has not yet been implemented. "
                "Please contact Noviat (info@noviat.com) for "
                "more information about the development roadmap", comm_type)
            st_line_name = transaction['name']
            st_line_comm = '\n' + INDENT + st_line_name
            st_line_comm += '\n' + INDENT + transaction['communication']
        return st_line_name, st_line_comm

    def _parse_comm_info_001(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = INDENT + st_line_name + ':'
        val = comm[0:70].strip()
        if val:
            st_line_comm += INDENT + _('Name') + ': %s' % val
        val = comm[70:105].strip()
        if val:
            st_line_comm += INDENT + _('Street') + ': %s' % val
        val = comm[105:140].strip()
        if val:
            st_line_comm += INDENT + _('Locality') + ': %s' % val
        val = comm[140:175].strip()
        if val:
            st_line_comm += INDENT + _('Identification Code') + ': %s' % val
        return st_line_name, st_line_comm

    def _parse_comm_info_002(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = comm.strip()
        return st_line_name, st_line_comm

    def _parse_comm_info_004(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = comm.strip()
        return st_line_name, st_line_comm

    def _parse_comm_info_005(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = comm.strip()
        return st_line_name, st_line_comm

    def _parse_comm_info_006(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        amount_sign = comm[48]
        amount = (amount_sign == '1' and '-' or '') \
            + ('%.2f' % list2float(comm[33:48])) + ' ' + comm[30:33]
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = INDENT + st_line_name + ':'
        st_line_comm += INDENT + _('Description of the detail') \
            + ': %s' % comm[0:30].strip()
        st_line_comm += INDENT + _('Amount') \
            + ': %s' % amount
        st_line_comm += INDENT + _('Category') \
            + ': %s' % comm[49:52].strip()
        return st_line_name, st_line_comm

    def _parse_comm_info_007(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = INDENT + st_line_name + ':'
        st_line_comm += INDENT + _('Number of notes/coins') \
            + ': %s' % comm[0:7]
        st_line_comm += INDENT + _('Note/coin denomination') \
            + ': %s' % comm[7:13]
        st_line_comm += INDENT + _('Total amount') \
            + ': %.2f' % list2float(comm[13:28])
        return st_line_name, st_line_comm

    def _parse_comm_info_008(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = INDENT + st_line_name + ':'
        st_line_comm += INDENT + _('Name') + ': %s' % comm[0:70].strip()
        st_line_comm += INDENT + _('Identification Code') \
            + ': %s' % comm[70:105].strip()
        return st_line_name, st_line_comm

    def _parse_comm_info_009(self, coda_statement, transaction):
        comm_type = transaction['struct_comm_type']
        comm = transaction['communication']
        st_line_name = filter(
            lambda x: x.code == comm_type,
            self._comm_types)[0].description
        st_line_comm = INDENT + st_line_name + ':'
        st_line_comm += INDENT + _('Name') + ': %s' % comm[0:70].strip()
        st_line_comm += INDENT + _('Identification Code') \
            + ': %s' % comm[70:105].strip()
        return st_line_name, st_line_comm
