# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models
import openerp.addons.decimal_precision as dp


class CodaBankStatement(models.Model):
    _name = 'coda.bank.statement'
    _description = 'CODA Bank Statement'
    _order = 'date desc'

    name = fields.Char(string='Name', required=True, readonly=True)
    date = fields.Date(string='Date', required=True, readonly=True)
    coda_creation_date = fields.Date(
        string='CODA Creation Date', readonly=True)
    old_balance_date = fields.Date(
        string='Old Balance Date', readonly=True)
    new_balance_date = fields.Date(
        string='New Balance Date', readonly=True)
    coda_id = fields.Many2one(
        'account.coda', string='CODA Data File', ondelete='cascade')
    type = fields.Selection(
        [('normal', 'Normal'),
         ('info', 'Info')],
        string='Type', required=True, readonly=True,
        help="No Bank Statements are associated with "
             "CODA Bank Statements of type 'Info'.")
    coda_bank_account_id = fields.Many2one(
        'coda.bank.account', string='Bank Account', readonly=True)
    balance_start = fields.Float(
        string='Starting Balance', digits_compute=dp.get_precision('Account'),
        readonly=True)
    balance_end_real = fields.Float(
        string='Ending Balance', digits_compute=dp.get_precision('Account'),
        readonly=True)
    line_ids = fields.One2many(
        'coda.bank.statement.line', 'statement_id',
        string='CODA Bank Statement lines', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True, readonly=True,
        help="The currency of the CODA Bank Statement")
    company_id = fields.Many2one(
        'res.company', related='coda_bank_account_id.company_id',
        string='Company',
        store=True, readonly=True)


class CodaBankStatementLine(models.Model):
    _name = 'coda.bank.statement.line'
    _order = 'sequence'
    _description = 'CODA Bank Statement Line'

    name = fields.Char(string='Communication', size=268, required=True)
    sequence = fields.Integer(string='Sequence')
    date = fields.Date(string='Entry Date', required=True)
    val_date = fields.Date(string='Value Date')
    type = fields.Selection(
        [('regular', 'Regular'),
         ('globalisation', 'Globalisation'),
         ('information', 'Information'),
         ('communication', 'Free Communication')],
        string='Type', required=True)
    globalisation_level = fields.Integer(
        string='Globalisation Level',
        help="The value which is mentioned (1 to 9), "
             "specifies the hierarchy level"
             " of the globalisation of which this record is the first."
             "\nThe same code will be repeated at the end "
             "of the globalisation.")
    globalisation_amount = fields.Float(
        string='Globalisation Amount',
        digits_compute=dp.get_precision('Account'))
    globalisation_id = fields.Many2one(
        'account.bank.statement.line.global',
        string='Globalisation ID', readonly=True,
        help="Code to identify transactions belonging to the "
             "same globalisation level within a batch payment")
    amount = fields.Float(
        string='Amount', digits_compute=dp.get_precision('Account'))
    statement_id = fields.Many2one(
        'coda.bank.statement', string='CODA Bank Statement',
        required=True, ondelete='cascade')
    coda_bank_account_id = fields.Many2one(
        'coda.bank.account',
        related='statement_id.coda_bank_account_id',
        string='Bank Account', store=True, readonly=True)
    ref = fields.Char(string='Reference')
    note = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', related='statement_id.company_id',
        string="Company", readonly=True, store=True)
