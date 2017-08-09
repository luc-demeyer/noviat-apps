# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models

import logging
_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self):
        context = self._context
        if context.get('default_model') in ['sale.order', 'account.invoice'] \
                and context.get('default_res_id'):
            # block auto-subscription
            ctx = dict(context,
                       mail_create_nosubscribe=True,
                       mail_post_autofollow=False)
            if context['default_model'] == 'sale.order' \
                    and context.get('mark_so_as_sent'):
                so = self.env['sale.order'].browse(context['default_res_id'])
                so.signal_workflow('quotation_sent')
                # block any further call to this type of routine
                # (since there is one in the original sale.py)
                ctx['mark_so_as_sent'] = False
            return super(
                MailComposeMessage, self.with_context(ctx)).send_mail()
        return super(MailComposeMessage, self).send_mail()
