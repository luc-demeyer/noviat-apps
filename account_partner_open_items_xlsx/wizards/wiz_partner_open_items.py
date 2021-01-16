# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WizPartnerOpenItems(models.TransientModel):
    _name = 'wiz.partner.open.items'
    _description = 'Open Items per partner at a given date'

    date_at = fields.Date(
        required=True,
        default=lambda self: self._default_date_at(),
        help="Specify a date in order to retrieve the Open Items "
             "at a certain moment in the past.")
    target_move = fields.Selection(
        selection=[('posted', 'All Posted Entries'),
                   ('all', 'All Entries')],
        string='Target Moves', default='all', required=True)
    result_selection = fields.Selection(
        selection=[('customer', 'Receivable Accounts'),
                   ('supplier', 'Payable Accounts'),
                   ('customer_supplier', 'Receivable and Payable Accounts')],
        string='Filter on', default='customer')
    partner_select = fields.Selection(
        selection=[('all', 'All Partners'),
                   ('select', 'Selected Partners')],
        string='Partners', required=True,
        default=lambda self: self._default_partner_select())
    add_currency = fields.Boolean(
        string='Show Currency',
        help='Show Foreign Currency')
    add_reconcile = fields.Boolean(
        string='Show Reconcile',
        help="Show Reconcile Details:"
             "\nThe identifiers of the matched Journal Items are added "
             "to the report in order to show which entries have been "
             "partially reconciled at the selected date."
             "\nIn case the entry has been fully reconciled "
             "after the selected date, the full reconcile reference "
             "will also be added as a value between brackets at the "
             "end of the Reconcile Details string."
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        column1='wiz_id',
        column2='partner_id',
        domain=[('parent_id', '=', False)],
        string='Partners',
        default=lambda self: self._default_partner_ids(),
        help="Leave blank to select all partners.")
    account_ids = fields.Many2many(
        comodel_name='account.account',
        column1='wiz_id',
        column2='account_id', string='Accounts',
        domain=[('reconcile', '=', True)],
        help="Leave blank to select all Receivable/Payable accounts"
             "You can use this field to select any general account that "
             "can be reconciled.")
    accounts = fields.Boolean(compute='_compute_accounts')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', readonly=True,
        default=lambda self: self._default_company_id())

    @api.model
    def _default_date_at(self):
        return fields.Date.today()

    @api.model
    def _default_partner_select(self):
        return 'select'

    @api.model
    def _default_partner_ids(self):
        partners = self.env['res.partner']
        pids = self.env.context.get('active_ids')
        if pids and self.env.context.get('active_model') == 'res.partner':
            partners = partners.browse(pids)
        return partners

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.account')

    @api.depends('account_ids')
    def _compute_accounts(self):
        self.accounts = self.account_ids and True or False

    @api.onchange('result_selection')
    def _onchange_result_selection(self):
        if self.result_selection:
            self.account_ids = False

    @api.onchange('account_ids')
    def _onchange_account_ids(self):
        if self.account_ids:
            self.result_selection = False

    @api.multi
    def xls_export(self):
        report = {
            'type': 'ir.actions.report.xml',
            'report_type': 'xlsx',
            'report_name': 'account_partner_open_items',
            'context': dict(self.env.context, xlsx_export=True),
            'datas': {'ids': [self.id]},
        }
        return report
