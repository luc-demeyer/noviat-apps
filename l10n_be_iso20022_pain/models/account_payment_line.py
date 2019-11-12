# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    communication_type = fields.Selection(
        selection_add=[
            ('bba', _('BBA Structured Communication')),
        ],
    )

    @api.model
    def check_bbacomm(self, val):
        supported_chars = '0-9'
        pattern = re.compile('[^' + supported_chars + ']')
        if pattern.findall(val or ''):
            return False
        if len(val) == 12:
            base = int(val[:10])
            mod = base % 97 or 97
            if mod == int(val[-2:]):
                return True
        return False

    @api.multi
    @api.constrains('communication', 'communication_type')
    def _check_communication(self):
        for rec in self:
            if rec.communication_type == 'bba'and \
                    not self.check_bbacomm(rec.communication):
                raise ValidationError(_(
                    "Invalid BBA Structured Communication !"))

    def invoice_reference_type2communication_type(self):
        res = super(AccountPaymentLine, self)\
            .invoice_reference_type2communication_type()
        res['bba'] = 'bba'
        return res
