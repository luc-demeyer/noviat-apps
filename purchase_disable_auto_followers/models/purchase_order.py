# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals, **kwargs):
        ctx = dict(self._context, mail_create_nosubscribe=True)
        return super(
            PurchaseOrder, self.with_context(ctx)).create(vals, **kwargs)

    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, context=None, **kwargs):
        if not context:
            context = {}
        context = dict(context,
                       mail_post_autofollow=False,
                       mail_create_nosubscribe=True)
        return super(PurchaseOrder, self).message_post(
            cr, uid, thread_id, context=context, **kwargs)

    @api.model
    def _message_get_auto_subscribe_fields(
            self, updated_fields, auto_follow_fields=None):
        """
        Turn off standard behavior (adding of 'user_id' partner)
        """
        return []
