# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('overdue_filter') and not count:
            partners = super(ResPartner, self).search(args)
            overdue_moves = self._get_overdue_moves(partners.ids)
            overdue_partners = overdue_moves.mapped('partner_id')
            partners = partners.filtered(
                lambda x: x.id in set(overdue_partners.ids))
            args.extend([('id', 'in', partners.ids)])
        return super(ResPartner, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def _get_overdue_moves(self, partner_ids,
                           company=None, account_select='all'):
        report_date = fields.Date.today()
        dom = [
            ('date_maturity', '<=', report_date),
            ('full_reconcile_id', '=', False),
            ('partner_id', 'in', partner_ids),
            ('partner_id.customer', '=', True),
        ]
        if account_select == 'receivable':
            dom.append(('account_id.internal_type', '=', 'receivable'))
        else:
            dom.append(
                ('account_id.internal_type', 'in', ['receivable', 'payable']))
        if company:
            dom.append(('company_id', '=', company.id))
        # Remark:
        # we may consider adding an option on the wizard
        # to add ('account_id.deprecated', '=', True/False)
        return self.env['account.move.line'].search(dom)
