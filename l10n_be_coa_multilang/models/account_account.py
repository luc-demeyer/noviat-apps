# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from openerp.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    financial_report_ids = fields.Many2many(
        comodel_name='account.financial.report',
        relation='account_account_financial_report',
        column1='account_id',
        column2='report_line_id',
        string='Financial Reports')

    @api.onchange('code')
    def _onchange_code(self):
        countries = self._get_be_scheme_countries()
        if self.code and \
                self.company_id.country_id.code in countries:
            update = []
            if self._origin.code:
                old = self._get_be_reportscheme_tag(self._origin.code)
                if old.report_id:
                    update.append((3, old.report_id.id))
            new = self._get_be_reportscheme_tag(self.code)
            if new.report_id:
                update.append((4, new.report_id.id))
            if update:
                self.financial_report_ids = update
            self.user_type_id = new.account_type_id
        if hasattr(super(AccountAccount, self), '_onchange_code'):
            super(AccountAccount, self)._onchange_code()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ improve performance of _update_be_reportscheme method """
        if self.env.context.get('update_be_reportscheme'):
            be_companies = self.env['res.company'].search([]).filtered(
                lambda r: r.country_id.code in self._get_be_scheme_countries()
            )
            args += [('company_id', 'in', [x.id for x in be_companies])]
        return super(AccountAccount, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id')
        if company_id:
            company = self.env['res.company'].browse(vals['company_id'])
        else:
            company = self.env[
                'res.company']._company_default_get('account.account')
        if company.country_id.code in self._get_be_scheme_countries():
            scheme_tag = self._get_be_reportscheme_tag(vals.get('code', ''))
            if scheme_tag:
                if scheme_tag.report_id:
                    vals['financial_report_ids'] = [
                        (4, scheme_tag.report_id.id)]
                if not vals.get('user_type_id'):
                    vals['user_type_id'] = scheme_tag.account_type_id.id
        return super(AccountAccount, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'code' in vals:
            if len(self) == 1 and vals.get('code') != self.code:
                company = vals.get('company_id') \
                    and self.env['res.company'].browse(vals['company_id']) \
                    or self.company_id
                if company.country_id.code in self._get_be_scheme_countries():
                    update = []
                    old = self._get_be_reportscheme_tag(self.code)
                    if old.report_id:
                        update.append((3, old.report_id.id))
                    new = self._get_be_reportscheme_tag(vals.get('code', ''))
                    if new.report_id:
                        update.append((4, new.report_id.id))
                    if update:
                        vals['financial_report_ids'] = vals.get(
                            'financial_report_ids', [])
                        vals['financial_report_ids'].append(update)
        return super(AccountAccount, self).write(vals)

    def _get_be_scheme_countries(self):
        """
        Use this method to extend the list of countries for which you want to
        use the Belgian BNB scheme for financial reporting purposes.
        """
        return ['BE']

    def _get_be_reportscheme_tag(self, code):
        scheme_tags = self.env[
            'be.legal.financial.reportscheme'].search([])
        scheme_tag = scheme_tags.filtered(
            lambda r: r.account_group == code[0:len(r.account_group)])
        if len(scheme_tag) > 1:
            raise UserError(
                _("Configuration Error in the "
                  "Belgian Legal Financial Report Scheme."))
        return scheme_tag
