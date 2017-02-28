# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def _acc_number_select(self, operator, number):
        """
        The code below could be simplified if the Odoo standard
        accounting modules would store bank account numbers
        in the database in 'normalised' format (without spaces or
        other formatting characters (such as '-').
        """
        if operator in ['=', '=like', '=ilike']:
            op = '='
        else:  # operator in ['like', 'ilike']
            op = 'LIKE'
        if len(number) == 12:
            """
            Belgium BBAN is always 12 chars and subset of IBAN.
            Hence we can retrieve the IBAN from a BBAN lookup.
            TODO: extend logic to other countries
            """
            select = \
                "SELECT id FROM res_partner_bank WHERE " \
                "(state='iban' AND SUBSTRING(acc_number FOR 2) = 'BE' AND " \
                "REPLACE(acc_number, ' ', '') LIKE '%%'|| '%s' ||'%%' ) " \
                % number
            # other countries
            if op == '=':
                select += "OR " \
                    "REPLACE(REPLACE(acc_number, ' ', ''), '-','') = '%s'" \
                    % number
            else:
                select += "OR " \
                    "REPLACE(REPLACE(acc_number, ' ', ''), '-','') " \
                    "LIKE '%%'|| '%s' ||'%%' " \
                    % number
        else:
            if op == '=':
                select = \
                    "SELECT id FROM res_partner_bank WHERE " \
                    "REPLACE(REPLACE(acc_number, ' ', ''), '-','') = '%s'" \
                    % number
            else:
                select = \
                    "SELECT id FROM res_partner_bank WHERE " \
                    "REPLACE(REPLACE(acc_number, ' ', ''), '-','') " \
                    "LIKE '%%'|| '%s' ||'%%' " \
                    % number
        return select

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        for i, arg in enumerate(args):
            if arg[0] == 'acc_number' and \
                    arg[1] in ['=', '=like', '=ilike', 'like', 'ilike']:
                number = arg[2].replace(' ', '').replace('-', '').upper()
                select = self._acc_number_select(arg[1], number)
                self._cr.execute(select)
                res = self._cr.fetchall()
                if res:
                    rpb_ids = [x[0] for x in res]
                    args[i] = ['id', 'in', rpb_ids]
        return super(ResPartnerBank, self).search(
            args, offset=offset, limit=limit, order=order, count=count)
