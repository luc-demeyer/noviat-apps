# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import time
from openerp import api, fields, models, _
# from openerp.exceptions import Warning as UserError
_logger = logging.getLogger(__name__)


class AccountReinvoiceWizard(models.TransientModel):
    _inherit = 'account.reinvoice.wizard'

    def _reinvoice_company(self, company):
        name = '%s - %s' % (company.name, fields.Datetime.now())
        log_state = 'draft'
        log_note = ''
        self._inv_count = 0
        self._error_count = 0

        self._log_note = ''
        self._err_log = ''
        log = self.env['account.reinvoice.batch.log'].create({
            'name': name,
            'state': log_state,
            'company_id': company.id,
            })

        mappings = self.env[
            'account.reinvoice.journal.mapping'].search(
            [('company_id', '=', company.id)])
        try:
            for mapping in mappings:
                wiz_vals = {
                    'company_id': company.id,
                    'journal_in_ids': [(6, 0, [mapping.journal_in_ids._ids])],
                    'journal_id': mapping.journal_id.id,
                    'refund_journal_id': mapping.refund_journal_id.id,
                    'income_account_id': mapping.income_account_id.id,
                    }
                wiz = self.create(wiz_vals)
                out_invoice_ids, out_refund_ids = wiz._generate()
                self._inv_count += len(out_invoice_ids) + len(out_refund_ids)
                if wiz.note:
                    self._log_note += wiz.note
        except Exception as e:
            self._error_count += 1
            self._err_log += _(
                "\nError in Reinvoice Service batch job "
                "for Company '%s'") % (company.name, str(e))

        if self._error_count:
            log_state = 'error'
        else:
            log_state = 'done'
        if self._err_log or self._log_note:
            log_note = self._err_log + self._log_note
        log.write({
            'note': log_note,
            'state': log_state,
            'inv_count': self._inv_count,
            'error_count': self._error_count,
            })

    @api.multi
    def _reinvoice_service(self):
        companies = self.sudo().env['res.company'].search([])
        time_start = time.time()
        _logger.warn('%s, Start Reinvoice Service batch job', self._name)
        for company in companies:
            ctx = dict(self._context, force_company=company.id)
            self.with_context(ctx).sudo()._reinvoice_company(company)
        duration = time.time() - time_start
        _logger.warn(
            '%s, Reinvoice Service batch job processing time = %.3f seconds',
            self._name, duration)
        return True
