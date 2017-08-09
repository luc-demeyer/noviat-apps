# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals, **kwargs):
        ctx = dict(self._context, mail_create_nosubscribe=True)
        return super(AccountInvoice, self.with_context(ctx)).create(
            vals, **kwargs)

    @api.multi
    def invoice_validate(self):
        """
        the portal_sale module (auto_install on ['sale', 'portal', 'payment'])
        forces the addition of the partner on validate.
        We undo this operation via 'disable_message_subscribe' in the context.
        """
        ctx = dict(self._context, disable_message_subscribe=True)
        return super(AccountInvoice, self.with_context(ctx)).invoice_validate()

    @api.multi
    def message_subscribe(self, partner_ids, subtype_ids=None):
        if self._context.get('disable_message_subscribe'):
            return True
        else:
            return super(AccountInvoice, self).message_subscribe(
                partner_ids, subtype_ids=subtype_ids)

    @api.model
    def _message_get_auto_subscribe_fields(
            self, updated_fields, auto_follow_fields=None):
        """
        Turn off standard behavior (adding of 'user_id' partner)
        """
        return []
