# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class account_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'

    module_l10n_account_translate = fields.Boolean(
        'Multilingual General Accounts',
        help="If checked, the General Account will become "
             "a multilingual field.")

    def execute(self, cr, uid, ids, context=None):
        """
        Relaunch the account chart setup wizard for multi-company setups
        """
        if not context:
            context = {}
        env = api.Environment(cr, uid, context)
        ctx = context.copy()
        wiz = self.browse(cr, uid, ids[0])
        if wiz.chart_template_id and wiz.chart_template_id.multilang_be:
            ctx.update({
                'company_id': wiz.company_id.id,
                'next_action': 'account.action_wizard_multi_chart',
            })
            todo = env.ref(
                'account.action_wizard_multi_chart_todo'
                )
            if todo.state == 'done':
                todo.state = 'open'
        return super(account_config_settings, self).execute(
            cr, uid, ids, context=ctx)

    def set_chart_of_accounts(self, cr, uid, ids, context=None):
        """
        the accounting setup will be triggered via the todo
        cf. execute method supra
        """
        config = self.browse(cr, uid, ids[0], context)
        if config.chart_template_id:
            assert config.expects_chart_of_accounts \
                and not config.has_chart_of_accounts
            if config.chart_template_id.multilang_be:
                return {}
        super(account_config_settings, self).set_chart_of_accounts(
            cr, uid, ids, context=context)


class res_config_configurable(models.TransientModel):
    _inherit = 'res.config'

    def _next(self, cr, uid, context=None):
        """
        update context for ir.actions.todo, cf. execute method supra
        """
        res = super(res_config_configurable, self)._next(cr, uid, context)
        if not context:
            context = {}
        if context.get('next_action') == 'account.action_wizard_multi_chart':
            ctx = res.get('context', {})
            ctx.update({
                'next_action': context['next_action'],
                'company_id': context['company_id']
            })
            res['context'] = ctx
        return res
