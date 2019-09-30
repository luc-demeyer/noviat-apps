# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountBankStatementLineGlobal(models.Model):
    _name = 'account.bank.statement.line.global'
    _description = 'Batch Payment Info'
    _rec_name = 'code'

    name = fields.Char(
        string='OBI', required=True, default='/',
        help="Originator to Beneficiary Information")
    code = fields.Char(
        required=True,
        default=lambda self: self._default_code())
    parent_id = fields.Many2one(
        comodel_name='account.bank.statement.line.global',
        string='Parent Code', ondelete='cascade')
    child_ids = fields.One2many(
        comodel_name='account.bank.statement.line.global',
        inverse_name='parent_id',
        string='Child Codes')
    type = fields.Selection(
        selection=[('iso20022', 'ISO 20022'),
                   ('coda', 'CODA'),
                   ('manual', 'Manual')],
        required=True)
    amount = fields.Monetary(
        currency_field='currency_id')
    payment_reference = fields.Char(
        help="Payment Reference. For SEPA (SCT or SDD) transactions, "
             "the PaymentInformationIdentification "
             "is recorded in this field.")
    bank_statement_line_ids = fields.One2many(
        comodel_name='account.bank.statement.line',
        inverse_name='globalisation_id',
        string='Bank Statement Lines')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', readonly=True,
        default=lambda self: self._default_company_id())
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True, readonly=True)

    _sql_constraints = [
        ('code_uniq',
         'unique (code, company_id)',
         'The code must be unique !')]

    @api.model
    def _default_code(self):
        res = self.env['ir.sequence'].next_by_code(
            'statement.line.global')
        return res

    @api.model
    def _default_company_id(self):
        c_id = self._context.get('force_company')
        if c_id:
            res = self.env['res.company'].browse(c_id)
        else:
            res = self.env.user.company_id
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            recs = self.search([('code', '=ilike', name)] + args, limit=limit)
            if not recs:
                recs = self.search(
                    [('name', operator, name)] + args, limit=limit)
            if not recs and len(name.split()) >= 2:
                # Separating code and name for searching
                # name can contain spaces
                operand1, operand2 = name.split(' ', 1)
                recs = self.search([
                    ('code', '=like', operand1), ('name', operator, operand2)
                ] + args, limit=limit)
        else:
            recs = self.browse()
        return recs.name_get()
