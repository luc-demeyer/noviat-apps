# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.report import report_sxw
from openerp import models
from openerp.tools.translate import translate

from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class overdue_payment(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(overdue_payment, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'format_vat': self._format_vat,
            'get_company_data': self._get_company_data,
            'get_partner_data': self._get_partner_data,
            'get_address': self._get_address,
            'getLines': self._lines_get,
            'message': self._message,
            'banks': self._banks_get,
        })
        self.context = context
        py_file = __name__.split('openerp.')[1].replace('.', '/') + '.py'
        self._ir_translation_name = py_file

    def _(self, src, lang):
        return translate(
            self.cr, self._ir_translation_name, 'code', lang, src) or src

    def set_context(self, objects, datas, ids, report_type=None):
        p_obj = self.pool['res.partner']
        self.open_moves = datas['open_moves']
        self.cpy = self.pool['res.company'].browse(
            self.cr, self.uid, datas['company_id'], context=self.context)
        self.report_date = datetime.strptime(
            datas['report_date'], '%Y-%m-%d').date()
        self.localcontext.update({
            'report_date': datas['report_date'],
            'company': self.cpy,
        })
        # Use the default invoice address of the partner
        new_objects = []
        for o in objects:
            c_id = p_obj.address_get(
                self.cr, self.uid, [o.id], ['invoice'])['invoice']
            invoice_contact = p_obj.browse(
                self.cr, self.uid, c_id)
            new_objects.append(invoice_contact)
        super(overdue_payment, self).set_context(
            new_objects, datas, ids, report_type=report_type)

    def _get_company_data(self):
        """
        Support is added for companies not subject to VAT via the
        'registry_number' field.
        Cf. l10n_be_partner for an example on how to add this field
        to res.partner
        """
        cpy = self.cpy
        p = cpy.partner_id
        res = '<b>' + p.name
        if p.title:
            res += ' ' + p.title.name
        res += '</b><br/>' + self._get_address(p)
        if p.vat:
            res += '<br/>' + self._format_vat(p.vat)
        elif hasattr(p, 'registry_number') and p.registry_number:
            res += '<br/>' + p.registry_number
        if cpy.company_registry:
            res += '<br/>' + cpy.company_registry
        return res

    def _get_partner_data(self, p):
        p_cpy = p.commercial_partner_id
        res = '<b>' + p_cpy.name
        if p_cpy.title:
            res += ' ' + p_cpy.title.name
        res += '</b>'
        if p.parent_id and not p.is_company:
            res += '<br/>' + self._("Attn.", p.lang) + ' '
            if p.title:
                res += p.title.name + ' '
            res += p.name
        res += '<br/>' + self._get_address(p)
        return res

    def _get_address(self, p):
        res = ''
        if p.street:
            res += p.street + '<br/>'
        if p.street2:
            res += p.street2 + '<br/>'
        if p.zip:
            cityline = p.zip + ' '
        else:
            cityline = ''
        if p.city:
            cityline += p.city
        if cityline:
            res += cityline
        if p.country_id:
            res += '<br/>' + p.country_id.name
        return res

    def _lines_get(self, partner):
        partner = partner.commercial_partner_id
        cr = self.cr
        uid = self.uid
        aml_obj = self.pool['account.move.line']
        company_currency = self.cpy.currency_id
        ar_ids = self.open_moves[str(partner.id)]['ar_ids']
        receivables = aml_obj.browse(cr, uid, ar_ids)
        ap_ids = self.open_moves[str(partner.id)]['ap_ids']
        payables = aml_obj.browse(cr, uid, ap_ids)
        lines = []
        for entry in (receivables + payables):
            currency = entry.currency_id
            sign = entry.credit and -1 or 1
            if currency and currency != self.cpy.currency_id:
                amount = entry.amount_currency
                amount_residual = sign * entry.amount_residual_currency
            else:
                amount = entry.debit or -entry.credit
                amount_residual = sign * entry.amount_residual
            if entry.reconcile_partial_id:
                amount_paid = (amount or 0.0) - (amount_residual or 0.0)
            else:
                amount_paid = 0.0
            if entry.date_maturity:
                maturity_date = datetime.strptime(
                    entry.date_maturity, '%Y-%m-%d').date()
                od_days = str((self.report_date - maturity_date).days)
            else:
                od_days = ''
            line = {
                'date': entry.date,
                'name': entry.name,
                'invoice_number': entry.invoice.number or '-',
                'date_maturity': entry.date_maturity or '',
                'amount': amount or 0.0,
                'amount_residual': amount_residual or 0.0,
                'amount_paid': amount_paid,
                'currency': currency or company_currency,
                'od_days': od_days,
                'od': entry.date_maturity and
                maturity_date <= self.report_date and 'X' or ''}
            lines.append(line)

        currencies = list(set([x['currency'] for x in lines]))
        totals = []
        for currency in currencies:
            lines_currency = filter(
                lambda x: x['currency'] == currency, lines)
            total_amount = reduce(
                lambda x, y: x + y,
                [x['amount'] for x in lines_currency])
            total_paid = reduce(
                lambda x, y: x + y,
                [x['amount_paid'] for x in lines_currency])
            total_residual = reduce(
                lambda x, y: x + y,
                [x['amount_residual'] for x in lines_currency])
            total_overdue = reduce(
                lambda x, y: x + y,
                [x['od'] and x['amount_residual'] or 0.0
                 for x in lines_currency])
            totals.append({
                'currency': currency,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'total_residual': total_residual,
                'total_overdue': total_overdue
            })

        return {'lines': lines, 'totals': totals}

    def _message(self, p):
        cr = self.cr
        uid = self.uid
        cpy = self.cpy
        cpy_obj = self.pool['res.company']
        user_obj = self.pool['res.users']
        message = cpy_obj.read(
            cr, uid, [cpy.id], ['overdue_msg'],
            context={'lang': p.lang})[0]['overdue_msg']
        user_signature = user_obj.browse(
            cr, uid, uid, self.context).signature or ''
        if message:
            message = message % {
                'partner_name': p.name,
                'date': self.report_date,
                'company_name': cpy.name,
                'user_signature': user_signature,
            }
        return message

    def _format_vat(self, vat):
        vat = vat or ''
        vat = vat.replace(' ', '').upper()
        if vat[0:2] == 'BE':
            vat = vat[0:2] + ' ' + '.'.join([vat[2:6], vat[6:9], vat[9:12]])
        return vat

    def _banks_get(self, company, count):
        # returns the first x banks (x = count)
        banks = filter(lambda x: x.footer, company.bank_ids)
        banks = banks[:count]
        bank_data = []
        for bank in banks:
            if bank.state == 'iban':
                bank_data.append(
                    'IBAN:' + bank.acc_number + ' BIC:' + bank.bank_bic)
            else:
                bank_data.append(bank.acc_number)
        return ' | '.join(bank_data)


class report_be_invoice(models.AbstractModel):
    _name = 'report.account_overdue.report_overdue'
    _inherit = 'report.abstract_report'
    _template = 'account_overdue.report_overdue'
    _wrapped_report_class = overdue_payment
