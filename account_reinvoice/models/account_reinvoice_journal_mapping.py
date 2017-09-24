# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class AccountReinvoiceJournalMapping(models.Model):
    _name = 'account.reinvoice.journal.mapping'
    _description = 'Reinvoice Journal Mapping'
    _order = 'sequence'

    sequence = fields.Integer(
        required=True, default=1)
    journal_in_ids = fields.Many2many(
        comodel_name='account.journal', string='Input Journals',
        domain="[('company_id', '=', company_id),"
               " ('type', 'not in', ['sale', 'sale_refund', 'situation'])]",
        required=True)
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Sales Journal',
        default=lambda self: self._default_journal_id(),
        domain="[('company_id', '=', company_id), ('type', '=', 'sale')]",
        required=True)
    refund_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Sales Refund Journal',
        default=lambda self: self._default_refund_journal_id(),
        domain="[('company_id', '=', company_id),"
               " ('type', '=', 'sale_refund')]",
        required=True)
    income_account_id = fields.Many2one(
        comodel_name='account.account', string='Default Income Account',
        help="Default Income Account. This value will be used for those "
             "outgoing invoice lines where the Income Account can not "
             "be retrieved via the Product Record configuration.")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)

    @api.model
    def _default_journal_id(self):
        company_id = self.env['res.company']._company_default_get(
            'account.reinvoice.wizard')
        domain = [
            ('company_id', '=', company_id),
            ('type', '=', 'sale')]
        journals = self.env['account.journal'].search(domain)
        if len(journals) == 1:
            return journals[0]
        else:
            return False

    @api.model
    def _default_refund_journal_id(self):
        company_id = self.env['res.company']._company_default_get(
            'account.reinvoice.wizard')
        domain = [
            ('company_id', '=', company_id),
            ('type', '=', 'sale_refund')]
        journals = self.env['account.journal'].search(domain)
        if len(journals) == 1:
            return journals[0]
        else:
            return False
