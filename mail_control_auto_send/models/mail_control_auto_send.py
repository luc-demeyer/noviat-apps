# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
import logging

from odoo import api, models, _
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class MailControlAutoSend(models.AbstractModel):
    _name = 'mail.control.auto.send'

    @api.model_cr
    def _register_hook(self):
        """
        logic copied from standard addons, module 'base_action_rule'.
        """

        def mail_control_create():

            @api.model
            def create(self, vals, **kw):
                ctx = dict(self._context, mail_auto_subscribe_no_notify=True)
                record = create.origin(self.with_context(ctx), vals, **kw)
                return record.with_env(self.env)

            return create

        to_patch_models = safe_eval(
            self.env['ir.config_parameter']
            .get_param('mail_disable_auto_send') or '[]')
        patched_models = defaultdict(set)

        def patch(model, name, method):

            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        for entry in to_patch_models:

            model = self.env.get(entry)
            if model is None:
                _logger.error(_(
                    "Configuration Error in system parameter '%s'."
                    "Model '%s' does not exist."
                ) % ('mail_disable_auto_send', entry))
                continue

            patch(model, 'create', mail_control_create())
