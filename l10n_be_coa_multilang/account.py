# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields


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
