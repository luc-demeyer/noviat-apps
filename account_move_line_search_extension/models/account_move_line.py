# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from lxml.builder import E
import re

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _get_default_amlse_view(self):
        element = E.field(name=self._rec_name_fallback())
        return E.tree(element, string=self._description)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):
        res = super(AccountMoveLine, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if self._context.get('account_move_line_search_extension') \
                and view_type in ['amlse', 'tree', 'form']:
            doc = etree.XML(res['arch'])
            tree = doc.xpath("/tree")
            for node in tree:
                if 'editable' in node.attrib:
                    del node.attrib['editable']
            form = doc.xpath("/form")
            for node in form:
                node.set('edit', 'false')
                node.set('create', 'false')
                node.set('delete', 'false')
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'account_move_line_search_extension' in self._context:
            for arg in args:

                if arg[0] == 'amount_search' and len(arg) == 3:
                    digits = self.env['decimal.precision'].precision_get(
                        'Account')
                    val = str2float(arg[2])
                    if val is not None:
                        if arg[2][0] in ['+', '-']:
                            f1 = 'balance'
                            f2 = 'amount_currency'
                        else:
                            f1 = 'abs(balance)'
                            f2 = 'abs(amount_currency)'
                            val = abs(val)
                        query = (
                            "SELECT id FROM account_move_line "
                            "WHERE round({0} - {2}, {3}) = 0.0 "
                            "OR round({1} - {2}, {3}) = 0.0"
                        ).format(f1, f2, val, digits)
                        self._cr.execute(query)
                        res = self._cr.fetchall()
                        ids = res and [x[0] for x in res] or [0]
                        arg[0] = 'id'
                        arg[1] = 'in'
                        arg[2] = ids
                    else:
                        arg[0] = 'id'
                        arg[1] = '='
                        arg[2] = 0
                    break

            for arg in args:
                if (
                    arg[0] == 'analytic_account_id' and
                    isinstance(arg[0], basestring)
                ):
                    ana_dom = ['|',
                               ('name', 'ilike', arg[2]),
                               ('code', 'ilike', arg[2])]
                    arg[2] = self.env['account.analytic.account'].search(
                        ana_dom).ids
                    break

        return super(AccountMoveLine, self).search(
            args, offset=offset, limit=limit, order=order, count=count)


def str2float(val):
    pattern = re.compile('[0-9]')
    dot_comma = pattern.sub('', val)
    if dot_comma and dot_comma[-1] in ['.', ',']:
        decimal_separator = dot_comma[-1]
    else:
        decimal_separator = False
    if decimal_separator == '.':
        val = val.replace(',', '')
    else:
        val = val.replace('.', '').replace(',', '.')
    try:
        return float(val)
    except:
        return None
