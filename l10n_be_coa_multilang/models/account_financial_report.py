# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models, _
from openerp.exceptions import Warning as UserError

import logging
_logger = logging.getLogger(__name__)


class be_legal_financial_reportscheme(models.Model):
    _name = 'be.legal.financial.reportscheme'
    _description = 'Belgian Legal Financial Report Scheme (Full)'
    _rec_name = 'account_group'
    _order = 'account_group'

    account_group = fields.Char(
        'Group', size=4, help='General Account Starting Digits')
    report_id = fields.Many2one(
        'account.financial.report', 'Report Entry', ondelete='cascade')
    account_ids = fields.Many2many(
        related='report_id.account_ids', string='Accounts', readonly=True)

    _sql_constraints = [
        ('group_uniq', 'unique (account_group)',
         'The General Account Group must be unique !')]


class account_financial_report(models.Model):
    _inherit = 'account.financial.report'

    code = fields.Char('Code', size=16)
    invisible = fields.Boolean(
        'Invisible', help="Hide this entry from the printed report.")

    def _get_children_by_order(self, cr, uid, ids, context=None):
        res = []
        if context.get('get_children_by_sequence'):
            res = self.search(
                cr, uid, [('id', 'child_of', ids[0]), ('invisible', '=', 0)],
                order='sequence ASC', context=context)
        else:
            res = super(
                account_financial_report, self)._get_children_by_order(
                    cr, uid, ids, context)
        return res


class account_account(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        help="this flag has an effect on the following reports:\n"
             "- Belgian legal BNB report : a 'centralized' account "
             "of type 'view' can be used as a substitute for its children "
             "(e.g. create a '400000' of type view whereby the children "
             "are of type 'receivable'\n"
             "- General Ledger report (the webkit one only), no details "
             "will be displayed in the General Ledger report "
             "(the webkit one only), only centralized amounts per period.")

    """
    _be_scheme_countries :
        override this attribute with the list of countries for which
        you want to use the Belgian BNB scheme
        for financial reporting purposes
    """
    _be_scheme_countries = ['BE']

    def search(self, cr, uid, args,
               offset=0, limit=None, order=None, context=None, count=False):
        """ improve performance of _update_be_reportscheme method """
        if context is None:
            context = {}
        if context.get('update_be_reportscheme'):
            be_scheme_company_ids = []
            company_obj = self.pool.get('res.company')
            company_ids = company_obj.search(cr, uid, [])
            for company_id in company_ids:
                company = company_obj.browse(
                    cr, uid, company_id, context=context)
                if company.country_id.code in self._be_scheme_countries:
                    be_scheme_company_ids.append(company_id)
            args += [('company_id', 'in', be_scheme_company_ids)]
        return super(account_account, self).search(
            cr, uid, args, offset, limit, order, context, count)

    def create(self, cr, uid, vals, context=None):
        acc_id = super(account_account, self).create(
            cr, uid, vals, context=context)
        scheme_obj = self.pool.get('be.legal.financial.reportscheme')
        scheme_table = scheme_obj.read(
            cr, uid,
            scheme_obj.search(cr, uid, []),
            ['account_group', 'report_id'],
            context=context)
        acc_code = vals['code']
        account = self.browse(cr, uid, acc_id, context=context)
        if account.type not in ['view', 'consolidation'] and \
                account.company_id.country_id.code in \
                self._be_scheme_countries:
            be_report_entries = filter(
                lambda x: acc_code[
                    0:len(x['account_group'])] == x['account_group'],
                scheme_table)
            if be_report_entries:
                if len(be_report_entries) > 1:
                    raise UserError(
                        _("Configuration Error !"),
                        _("Configuration Error in the "
                          "Belgian Legal Financial Report Scheme."))
                be_report_id = be_report_entries[0]['report_id'][0]
                self.write(
                    cr, uid, account.id,
                    {'financial_report_ids': [(4, be_report_id)]})
        return acc_id

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if 'code' in vals.keys() or 'type' in vals.keys():
            scheme_obj = self.pool.get('be.legal.financial.reportscheme')
            scheme_table = scheme_obj.read(
                cr, uid,
                scheme_obj.search(cr, uid, []),
                ['account_group', 'report_id'],
                context=context)
            be_report_ids = [x['report_id'][0] for x in scheme_table]
            acc_code = vals.get('code')
            acc_type = vals.get('type')
            centralized = vals.get('centralized')
            for account in self.browse(cr, uid, ids, context=context):
                updated = False
                if account.company_id.country_id.code in \
                        self._be_scheme_countries:
                    acc_code = acc_code or account.code
                    acc_type = acc_type or account.type
                    centralized = centralized or account.centralized
                    be_report_entries = filter(
                        lambda x: acc_code[
                            0:len(x['account_group'])] == x['account_group'],
                        scheme_table)
                    if len(be_report_entries) > 1:
                        raise UserError(
                            _("Configuration Error !"),
                            _("Configuration Error in the "
                              "Belgian Legal Financial Report Scheme."))
                    be_report_id = be_report_entries and \
                        be_report_entries[0]['report_id'][0]
                    for fin_report in account.financial_report_ids:
                        if fin_report.id in be_report_ids:
                            if acc_type not in ['view', 'consolidation'] \
                                    and fin_report.id == be_report_id:
                                updated = True
                            elif acc_type == 'view' and centralized \
                                    and fin_report.id == be_report_id:
                                updated = True
                            else:
                                vals.update({
                                    'financial_report_ids':
                                        [(3, fin_report.id)]})
                                updated = True
                    if be_report_id and (
                        acc_type not in ['view', 'consolidation'] or
                        (acc_type == 'view' and centralized)
                    ) and not updated:
                        vals.update(
                            {'financial_report_ids': [(4, be_report_id)]})
        return super(account_account, self).write(
            cr, uid, ids, vals, context=context)
