# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CodaAccountMappingRule(models.Model):
    _name = 'coda.account.mapping.rule'
    _description = 'Rules Engine to assign accounts during CODA parsing'
    _order = 'sequence'

    coda_bank_account_id = fields.Many2one(
        comodel_name='coda.bank.account',
        string='CODA Bank Account', ondelete='cascade')
    sequence = fields.Integer(
        string='Sequence',
        help='Determines the order of the rules to assign accounts')
    name = fields.Char(string='Rule Name', required=True)
    active = fields.Boolean(
        default=True, help='Switch on/off this rule.')
    # matching criteria
    partner_name = fields.Char(
        help="The name of the partner in the CODA Transaction."
             "\nYou can use this field to set a matching rule "
             "on Partners which are not (yet) registered in Odoo. ")
    counterparty_number = fields.Char(
        string="Account Number",
        help="The Bank Account Number of the Partner "
             "in the CODA Transaction."
             "\nYou can use this field to set a matching rule "
             "on Partners which are not (yet) registered in Odoo. ")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', ondelete='cascade',
        domain=['|', ('parent_id', '=', False), ('is_company', '=', True)],
        help="Use this field only if you have checked the 'Find Partner' "
             "option.")
    trans_type_id = fields.Many2one(
        comodel_name='account.coda.trans.type',
        string='Transaction Type')
    trans_family_id = fields.Many2one(
        comodel_name='account.coda.trans.code',
        string='Transaction Family',
        domain=[('type', '=', 'family')])
    trans_code_id = fields.Many2one(
        comodel_name='account.coda.trans.code',
        string='Transaction Code',
        domain=[('type', '=', 'code')])
    trans_category_id = fields.Many2one(
        comodel_name='account.coda.trans.category',
        string='Transaction Category')
    freecomm = fields.Char(string='Free Communication', size=128)
    struct_comm_type_id = fields.Many2one(
        comodel_name='account.coda.comm.type',
        string='Structured Communication Type')
    structcomm = fields.Char(string='Structured Communication', size=128)
    payment_reference = fields.Char(
        string='Payment Reference', size=35,
        help="Payment Reference. For SEPA (SCT or SDD) transactions, "
             "the EndToEndReference is recorded in this field.")
    # the split flag is required for the l10n_be_coda_card_cost module
    split = fields.Boolean(
        help="Split line into two separate lines with "
             "transaction amount and transaction cost.")
    # results
    account_id = fields.Many2one(
        comodel_name='account.account', string='Account',
        ondelete='cascade',
        domain=[('deprecated', '=', False)])
    account_tax_id = fields.Many2one(
        comodel_name='account.tax', string='Tax', ondelete='cascade')
    tax_type = fields.Selection(
        selection=[('base', 'Base'),
                   ('tax', 'Tax')])
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Analytic Account',
        ondelete='set null')

    @api.model
    def create(self, vals):
        self._strip_char_fields(vals)
        return super().create(vals)

    @api.multi
    def write(self, vals):
        self._strip_char_fields(vals)
        return super().write(vals)

    def _strip_char_fields(self, vals):
        for fld in self._get_strip_char_fields():
            if vals.get(fld):
                vals[fld] = vals[fld].strip()

    @api.model
    def rule_get(self, coda_bank_account_id,
                 partner_name=None, counterparty_number=None, partner_id=None,
                 trans_type_id=None, trans_family_id=None,
                 trans_code_id=None, trans_category_id=None,
                 struct_comm_type_id=None,
                 freecomm=None, structcomm=None, payment_reference=None,
                 split=False):

        select = (
            "SELECT partner_name, counterparty_number, partner_id, "
            "trans_type_id, trans_family_id, trans_code_id, "
            "trans_category_id, "
            "struct_comm_type_id, freecomm, structcomm, "
            "account_id, analytic_account_id, account_tax_id, tax_type, "
            "payment_reference")
        select += self._rule_select_extra(coda_bank_account_id) + ' '
        select += (
            "FROM coda_account_mapping_rule "
            "WHERE active = True AND coda_bank_account_id = %s "
            "AND COALESCE(split, False) = %s "
            "ORDER BY sequence") % (coda_bank_account_id, split)
        self._cr.execute(select)
        rules = self._cr.dictfetchall()
        condition = (
            "(not rule['partner_name'] or "
            "(partner_name == rule['partner_name'])) and "
            "(not rule['counterparty_number'] or "
            "(counterparty_number == rule['counterparty_number'])) and "
            "(not rule['trans_type_id'] or "
            "(trans_type_id == rule['trans_type_id'])) and "
            "(not rule['trans_family_id'] or "
            "(trans_family_id == rule['trans_family_id'])) "
            "and (not rule['trans_code_id'] or "
            "(trans_code_id == rule['trans_code_id'])) and "
            "(not rule['trans_category_id'] or "
            "(trans_category_id == rule['trans_category_id'])) "
            "and (not rule['struct_comm_type_id'] or "
            "(struct_comm_type_id == rule['struct_comm_type_id'])) and "
            "(not rule['partner_id'] or "
            "(partner_id == rule['partner_id'])) "
            "and (not rule['freecomm'] or (rule['freecomm'].lower() in "
            "(freecomm and freecomm.lower() or ''))) "
            "and (not rule['structcomm'] or "
            "(rule['structcomm'] in (structcomm or ''))) "
            "and (not rule['payment_reference'] or "
            "(rule['payment_reference'] in (payment_reference or ''))) ")
        result_fields = [
            'account_id', 'account_tax_id', 'tax_type', 'analytic_account_id']
        result_fields += self._rule_result_extra(coda_bank_account_id)
        res = {}
        for rule in rules:
            if eval(condition):
                for f in result_fields:
                    res[f] = rule[f]
                break
        return res

    def _rule_select_extra(self, coda_bank_account_id):
        """
        Use this method to customize the mapping rule engine.
        Cf. l10n_be_coda_analytic_plan module for an example.
        """
        return ''

    def _rule_result_extra(self, coda_bank_account_id):
        """
        Use this method to customize the mapping rule engine.
        Cf. l10n_be_coda_analytic_plan module for an example.
        """
        return []

    def _get_strip_char_fields(self):
        return ['partner_name', 'counterparty_number']
