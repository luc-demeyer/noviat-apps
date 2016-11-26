# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class account_account_type(models.Model):
    _inherit = 'account.account.type'
    active = fields.Boolean(string='Active', select=True, default=True)
    company_id = fields.Many2one('res.company', string='Company')


class account_account_template(models.Model):
    _inherit = 'account.account.template'
    name = fields.Char(translate=True)


class account_tax_template(models.Model):
    _inherit = 'account.tax.template'
    name = fields.Char(translate=True)


class account_tax_code_template(models.Model):
    _inherit = 'account.tax.code.template'
    name = fields.Char(translate=True)


class account_chart_template(models.Model):
    _inherit = 'account.chart.template'
    _order = 'name'
    name = fields.Char(translate=True)
    multilang_be = fields.Boolean(string='Multilang Belgian CoA')
    bank_from_template = fields.Boolean(
        string='Banks/Cash from Template',
        help="Generate Bank/Cash accounts and journals from the Templates.")


class account_fiscal_position_template(models.Model):
    _inherit = 'account.fiscal.position.template'
    name = fields.Char(translate=True)
    note = fields.Text(translate=True)


class account_journal(models.Model):
    _inherit = 'account.journal'
    name = fields.Char(translate=True)
