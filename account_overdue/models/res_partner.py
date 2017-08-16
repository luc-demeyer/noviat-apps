# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_overdue_partners(self, report_date, company_id, partner_ids,
                              account_select):
        """
        Select AR/AP moves and remove partially reconciled
        receivables/payables since these are on the report
        via the 'Amount Paid'.

        The following logic is used for this removal;
        Receivables: keep only Credit moves
        Payables: keep only Debit moves
        """
        def remove_filter(line):
            if line['reconcile_partial_id']:
                if line['type'] == 'receivable' and line['credit']:
                    return True
                elif line['type'] == 'payable' and line['debit']:
                    return True
            return False
        partners = set(
            [x.commercial_partner_id for x in self.browse(partner_ids)])

        overdue_partners = self.env['res.partner']
        open_moves = {}

        for partner in partners:

            self._cr.execute(
                "SELECT l.id, a.type, a.code, "
                "l.debit, l.credit, l.reconcile_partial_id, "
                "(CASE WHEN l.date_maturity IS NOT NULL THEN l.date_maturity "
                "ELSE ai.date_due END) AS date_maturity "
                "FROM account_move_line l "
                "INNER JOIN account_account a ON l.account_id = a.id "
                "INNER JOIN account_move am ON l.move_id = am.id "
                "LEFT OUTER JOIN account_invoice ai ON ai.move_id = am.id "
                "LEFT OUTER JOIN res_partner p ON l.partner_id = p.id "
                "WHERE l.partner_id = %s "
                "AND a.type IN ('receivable', 'payable') "
                "AND l.state != 'draft' AND l.reconcile_id IS NULL "
                "AND l.company_id = %s AND p.customer = TRUE "
                "AND (l.debit + l.credit) != 0 "
                "ORDER BY date_maturity",
                (partner.id, company_id)
            )
            all_lines = self._cr.dictfetchall()
            removes = filter(remove_filter, all_lines)
            remove_ids = [x['id'] for x in removes]
            lines = filter(lambda x: x['id'] not in remove_ids, all_lines)

            receivables = payables = []
            ar_filter = self._ar_filter()
            ap_filter = self._ap_filter()
            if account_select == 'receivable':
                receivables = filter(
                    ar_filter, lines)
            if account_select == 'all':
                receivables = filter(
                    ar_filter, lines)
                payables = filter(
                    ap_filter, lines)
                # remove payables which have been partially
                # reconciled with receivables
                ar_rec_partial_ids = [
                    x['reconcile_partial_id'] for x in filter(
                        lambda x: x['reconcile_partial_id'], receivables)]
                payables = filter(
                    lambda x: x['reconcile_partial_id'] not in
                    ar_rec_partial_ids, payables)

            # remove the partners with no entries beyond the maturity date
            overdues = filter(
                lambda x: x['date_maturity'] and
                x['date_maturity'] <= report_date,
                receivables + payables)
            if not overdues:
                continue

            ar_ids = [x['id'] for x in receivables]
            ap_ids = [x['id'] for x in payables]
            if ar_ids or ap_ids:
                open_moves[str(partner.id)] = {
                    'ar_ids': ar_ids,
                    'ap_ids': ap_ids,
                }
                overdue_partners += partner

        return overdue_partners, open_moves

    def _ar_filter(self):
        return lambda x: x['type'] == 'receivable'

    def _ap_filter(self):
        return lambda x: x['type'] == 'payable'

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        if not context:
            context = {}

        if context.get('overdue_filter'):
            env = api.Environment(cr, uid, context)
            report_date = fields.Datetime.context_timestamp(
                env['res.partner'], datetime.now()).date()
            report_date = report_date.strftime('%Y-%m-%d')
            company = env.user.company_id
            account_select = 'all'
            partner_ids = super(ResPartner, self).search(
                cr, uid, args, context=context)
            overdue_partners, open_moves = self._get_overdue_partners(
                cr, uid, report_date, company.id, partner_ids, account_select,
                context=context)
            args.append(('id', 'in', overdue_partners._ids))

        return super(ResPartner, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order,
            context=context, count=count)
