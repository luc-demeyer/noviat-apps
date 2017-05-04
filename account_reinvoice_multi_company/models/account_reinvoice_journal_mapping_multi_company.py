# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class AccountReinvoiceJournalMappingMultiCompany(models.Model):
    _name = 'account.reinvoice.journal.mapping.multi.company'
    _description = 'Reinvoice Journal Mapping multi-company'
    _order = 'sequence,target_company'

    sequence = fields.Integer(
        required=True, default=10)
    journal_out_ids = fields.Many2many(
        comodel_name='account.journal', string='Output Journals',
        relation='journal_reinvoice_mapping_multi_company_rel',
        domain="[('company_id', '=', company_id),"
               " ('type', 'in', ['sale', 'sale_refund'])]",
        required=True)
    target_company = fields.Selection(
        selection='_selection_target_company',
        string='Target Company', required=True)
    target_journal = fields.Many2one(
        comodel_name='account.journal.multi.company.list',
        domain="[('type', '=', 'purchase'),"
               " ('company_id', '=', target_company)]",
        string='Target Journal', required=True)
    target_refund_journal = fields.Many2one(
        comodel_name='account.journal.multi.company.list',
        domain="[('type', '=', 'purchase_refund'),"
               " ('company_id', '=', target_company)]",
        string='Target Refund Journal', required=True)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        required=True, readonly=True,
        default=lambda self: self.env.user.company_id)

    @api.model
    def _selection_target_company(self):
        domain = self._selection_target_company_domain()
        companies = self.env['res.company'].sudo().search(domain)
        return [(str(c.id), c.name) for c in companies]

    def _selection_target_company_domain(self):
        return [('id', '!=', self.env.user.company_id.id)]

    @api.onchange('target_company')
    def _onchange_target_company(self):
        if self.target_company:
            self.target_journal = False
            self.target_refund_journal = False
