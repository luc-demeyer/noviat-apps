# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from openerp import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit')

    @api.multi
    def onchange_journal_id(self, journal_id):
        res = super(AccountBankStatement, self).onchange_journal_id(journal_id)
        journal = self.env['account.journal'].browse(journal_id)
        ou = journal.default_debit_account_id.operating_unit_id
        if not ou:
            ou = self.env['res.users'].operating_unit_default_get(self._uid)
        ou_id = ou and ou.id
        if not res:
            res = {'value': {'operating_unit_id': ou_id}}
        else:
            res['value']['operating_unit_id'] = ou_id
        return res
