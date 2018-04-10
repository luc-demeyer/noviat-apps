# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    active = fields.Boolean(default=True)
