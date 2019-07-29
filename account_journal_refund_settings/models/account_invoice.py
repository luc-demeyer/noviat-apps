# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# mapping invoice type to journal type
_T2T = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}
# mapping invoice type to journal refund_usage
_T2U = {
    'out_invoice': ['both', 'regular'],
    'out_refund': ['both', 'refund'],
    'in_invoice': ['both', 'regular'],
    'in_refund': ['both', 'refund']}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    journal_id = fields.Many2one(
        default=lambda self: self._default_journal(),
        domain="[('type', '=', {}.get(type)), "
               "('refund_usage', 'in', {}.get(type)), "
               "('company_id', '=', company_id)]".format(_T2T, _T2U),
    )

    @api.model
    def _default_journal(self):
        if self.env.context.get('default_journal_id'):
            return super()._default_journal()
        inv_type = self.env.context.get('type', 'out_invoice')
        j_type = _T2T.get(inv_type)
        j_refund_usage = _T2U.get(inv_type)
        if j_type and j_refund_usage:
            company_id = self.env.context.get(
                'company_id', self.env.user.company_id.id)
            j_dom = [
                ('type', '=', j_type),
                ('refund_usage', 'in', j_refund_usage),
                ('company_id', '=', company_id)]
            journals = self.env['account.journal'].search(j_dom)
            if len(journals) == 1:
                return journals
            else:
                if not self.env.context.get('active_model'):
                    # return empty journal to enforce manual selection
                    return self.env['account.journal']
                elif self.env.context.get('active_model') == 'sale.order':
                    journals = self._guess_sale_order_journals(journals)
                    if len(journals) == 1:
                        return journals
                # purchase.order: journal selection via onchange,
                #     cf. account_journal_refund_settings_purchase module

        return super()._default_journal()

    def _guess_sale_order_journals(self, journals):
        """
        You can use this method to add your own logic when
        there are multiple sale journals.
        As an alternative we suggest to inherit the sale.order object and
        use customer specific logic to select the appropriate
        sales journal and add this one to the context via the
        'default_journal_id' key.

        The code below covers the case where the POS is installed
        and configured with a seperate sales journal for the POS orders.
        """
        if 'pos.config' in self.env:
            pos_configs = self.env['pos.config'].sudo().search([])
            for pos_config in pos_configs:
                if pos_config.journal_id != pos_config.invoice_journal_id:
                    journals -= pos_config.journal_id
        return journals

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        vals = super()._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        journal = self.env['account.journal'].browse(journal_id)
        refund_journal = journal.refund_journal_id
        if not refund_journal:
            if journal.refund_usage == 'both':
                refund_journal = journal
        vals['journal_id'] = refund_journal.id
        return vals
