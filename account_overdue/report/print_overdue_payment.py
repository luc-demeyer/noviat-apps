# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import translate
from functools import reduce


IR_TRANSLATION_NAME = __name__.split('odoo.')[1].replace('.', '/') + '.py'


class OverduePayment(models.AbstractModel):
    _name = 'report.account_overdue.report_overdue'
    _description = 'Overdue Payment Report'

    def _(self, src, lang):
        return translate(
            self.env.cr, IR_TRANSLATION_NAME, 'code', lang, src) or src

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Select open AR/AP moves and remove partially reconciled
        receivables/payables since these are on the report
        via the 'amount_paid'.

        The following logic is used for this removal;
        Receivables: keep only Debit moves
        Payables: keep only Credit moves
        """
        wiz = self.env['overdue.payment.wizard'].browse(data['wiz_id'])
        dom = [('company_id', '=', wiz.company_id.id)]
        if wiz.partner_select == 'select':
            dom.append(('id', 'in', data['partner_ids']))
        partners = self.env['res.partner'].search(dom)
        overdue_moves = self.env['res.partner']._get_overdue_moves(
            partners.ids, company=wiz.company_id,
            account_select=wiz.account_select)
        if not overdue_moves:
            raise UserError(_(
                "No overdue transactions found for your selection!"
            ))
        self.cpy = wiz.company_id
        self.report_date = fields.Datetime.context_timestamp(
            self.env.user, datetime.now())

        def account_type_filter(aml):
            types = ['receivable']
            if wiz.account_select == 'all':
                types.append('payable')
            return aml.account_id.internal_type in types

        open_moves = overdue_moves.filtered(account_type_filter)

        def remove_filter(aml):
            if aml.account_id.internal_type == 'receivable' and aml.credit:
                if aml.matched_debit_ids:
                    return True
            elif aml.account_id.internal_type == 'payable' and aml.debit:
                if aml.matched_credit_ids:
                    return True
            return False

        removes = open_moves.filtered(remove_filter)
        amls = open_moves - removes
        overdue_partners = amls.mapped('partner_id')

        amls_by_partner = {}
        for aml in amls:
            pid = aml.partner_id.id
            if pid in amls_by_partner:
                amls_by_partner[pid] += aml
            else:
                amls_by_partner[pid] = aml
        self.amls_by_partner = amls_by_partner

        # Use the default invoice address of the partner
        contacts = self.env['res.partner']
        for partner in overdue_partners:
            contact_id = partner.address_get(['invoice'])['invoice']
            contact = self.env['res.partner'].browse(contact_id)
            contacts += contact

        return {
            'overdue.payment.wizard': wiz,
            'company': wiz.company_id,
            'partners': contacts,
            'format_vat': self._format_vat,
            'get_company_data': self._get_company_data,
            'get_partner_data': self._get_partner_data,
            'get_address': self._get_address,
            'getLines': self._lines_get,
            'message': self._message,
            'banks': self._banks_get,
        }

    def _get_company_data(self):
        """
        Support is added for companies not subject to VAT via the
        'kbo_bce_number' field.
        Cf. l10n_be_partner_kbo_bce for an example on how to add this field
        to res.partner
        Adapt this method for use with other localisation modules.
        """
        cpy = self.cpy
        p = cpy.partner_id
        res = '<b>' + p.name
        if p.title:
            res += ' ' + p.title.name
        res += '</b><br/>' + self._get_address(p)
        vat_or_kbo = False
        if p.vat:
            vat_or_kbo = p.vat
            res += '<br/>' + self._format_vat(p.vat)
        elif hasattr(p, 'kbo_bce_number') and p.kbo_bce_number:
            vat_or_kbo = p.kbo_bce_number
            res += '<br/>' + p.kbo_bce_number
        if cpy.company_registry:
            vat_or_kbo = vat_or_kbo.replace(' ', '').replace('.', '')
            cpy_reg = cpy.company_registry.replace(' ', '').replace('.', '')
            if cpy_reg not in vat_or_kbo:
                res += '<br/>' + cpy.company_registry
        return res

    def _get_partner_data(self, p):
        p_cpy = p.commercial_partner_id
        res = '<b>' + p_cpy.name
        if p_cpy.title:
            res += ' ' + p_cpy.title.name
        res += '</b>'
        if p.parent_id and not p.is_company:
            if p.name:
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

    def _lines_get(self, contact):
        partner = contact.commercial_partner_id
        amls = self.amls_by_partner[partner.id]
        receivables = amls.filtered(
            lambda x: x.account_id.internal_type == 'receivable')
        payables = amls - receivables
        receivables = receivables.sorted(key=lambda r: r.date)
        payables = payables.sorted(key=lambda r: r.date)
        company_currency = self.cpy.currency_id
        lines = []
        entries = (receivables + payables).with_context(lang=contact.lang)
        for entry in entries:
            currency = entry.currency_id
            if currency and currency != company_currency:
                amount = entry.amount_currency
                amount_residual = entry.amount_residual_currency
            else:
                amount = entry.balance
                amount_residual = entry.amount_residual
            amount_paid = amount - amount_residual
            maturity_date = datetime.strptime(
                entry.date_maturity, '%Y-%m-%d')
            maturity_date = fields.Datetime.context_timestamp(
                self.env.user, maturity_date)
            od_days = str((self.report_date - maturity_date).days)

            line = {
                'invoice_number': entry.invoice_id.number or '-',
                'amount': amount or 0.0,
                'amount_residual': amount_residual or 0.0,
                'amount_paid': amount_paid,
                'currency': currency or company_currency,
                'od_days': od_days,
                'od': maturity_date <= self.report_date and 'X' or '',
                'entry': entry,
            }
            lines.append(line)

        currencies = list(set([x['currency'] for x in lines]))
        totals = []
        for currency in currencies:
            lines_currency = [x for x in lines if x['currency'] == currency]
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

    def _message_date_string(self, p):
        return '%(date)s<br/>'

    def _message(self, p):
        lang_code = p.lang or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        report_date = self.report_date.strftime(date_format)
        message = self.cpy.with_context({'lang': p.lang}).overdue_msg
        if '%(date)s' not in message:
            message = self._message_date_string(p) + message
        message = message.replace('\n', '<br/>')
        user_signature = self.env.user.signature or ''
        if message:
            message = message % {
                'partner_name': p.name,
                'date': report_date,
                'company_name': self.cpy.name,
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
        banks = company.bank_journal_ids.filtered(
            lambda r: r.display_on_footer).mapped('bank_account_id')
        banks = banks[:count]
        bank_data = []
        for bank in banks:
            if bank.acc_type == 'iban':
                bank_data.append(
                    'IBAN:' + bank.acc_number + ' BIC:' + bank.bank_bic)
            else:
                bank_data.append(bank.acc_number)
        return ' | '.join(bank_data)
