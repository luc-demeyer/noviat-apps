# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

# mapping invoice type to refund type
_T2T = {
    'out_invoice': 'out_refund',
    'in_invoice': 'in_refund',
    'out_refund': 'out_invoice',
    'in_refund': 'in_invoice',
}


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    @api.multi
    def compute_refund(self, mode='refund'):
        res = super().compute_refund(mode=mode)
        active_ids = self.env.context.get('active_ids')
        if len(active_ids) == 1 and isinstance(res, dict):
            invoice = self.env['account.invoice'].browse(active_ids)
            if self.filter_refund in ['refund', 'cancel']:
                refund_type = _T2T.get(invoice.type)
                domain = res.get('domain')
                if domain and 'refund' in refund_type:
                    module = 'account_refund_menu'
                    action = '{}.account_invoice_action_{}'.format(
                        module, refund_type)
                    res = self.env.ref(action).read()[0]
                    for i, arg in enumerate(domain):
                        if arg[0] == 'type':
                            domain[i] = ('type', '=', refund_type)
                    res['domain'] = domain
        return res
