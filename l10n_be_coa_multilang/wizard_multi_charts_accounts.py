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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class wizard_multi_charts_accounts(models.TransientModel):
    """
    Change wizard that creates a new account chart for a company.
        * update company_id country to Belgium
        * load nl & fr languages
        * Replace creation of financial accounts by copy from template.
          This change results in adherence to Belgian MAR numbering scheme
          for cash accounts.
    """
    _inherit = 'wizard.multi.charts.accounts'

    load_nl_BE = fields.Boolean('Load Dutch (nl_BE) Translation')
    load_fr_BE = fields.Boolean('Load French (fr_BE) Translation')
    load_nl_NL = fields.Boolean('Load Dutch (nl_NL) Translation')
    load_fr_FR = fields.Boolean('Load French (fr_FR) Translation')
    multilang_be = fields.Boolean('Multilingual Belgian CoA')
    multilang_coa = fields.Boolean(
        'Multilingual Chart of Accounts',
        help="If checked, the General Account will become "
             "a multilingual field. \n"
             "THis behaviour can be changed afterwards via "
             "Settings -> Configuration -> Accounting")

    @api.model
    def _coa_lang(self):
        res = self._context.get('lang')
        res = res and res[:2]
        return res in ['fr', 'nl'] and res or 'en'

    coa_lang = fields.Selection(
        [('en', 'English'),
         ('fr', 'French'),
         ('nl', 'Dutch')],
        string='Chart of Accounts Language',
        default=_coa_lang,
        help="Select the language of the Chart Of Accounts")

    @api.model
    def _default_company(self):
        res = self._context.get('company_id')
        if not res:
            res = self.env.user.company_id.id
        return res

    company_id = fields.Many2one(default=_default_company)

    def default_get(self, cr, uid, fields, context=None):
        if not context:
            context = {}
        res = super(wizard_multi_charts_accounts, self).default_get(
            cr, uid, fields, context)
        if res.get('chart_template_id'):
            chart_template = self.pool['account.chart.template'].browse(
                cr, uid, res['chart_template_id'], context=context)
            res['multilang_be'] = chart_template.multilang_be
        if 'company_id' in context:
            res['company_id'] = context['company_id']
        return res

    def onchange_chart_template_id(self, cr, uid, ids,
                                   chart_template_id=False, context=None):
        res = super(
            wizard_multi_charts_accounts, self).onchange_chart_template_id(
                cr, uid, ids, chart_template_id, context=context)
        obj_chart_template = self.pool.get('account.chart.template')
        res_update = {}
        if chart_template_id:
            chart_template = obj_chart_template.browse(
                cr, uid, chart_template_id, context=context)
            multilang_be = chart_template.multilang_be
            res_update['multilang_be'] = multilang_be
        res['value'].update(res_update)
        return res

    def onchange_lang(self, cr, uid, ids,
                      load_nl_BE, load_fr_BE, load_nl_NL, load_fr_FR):
        res = {}
        value = {}
        if load_nl_BE or load_fr_BE:
            if load_nl_NL:
                value['load_nl_NL'] = False
            if load_fr_FR:
                value['load_fr_FR'] = False
        elif load_nl_NL or load_fr_FR:
            if load_nl_BE:
                value['load_nl_BE'] = False
            if load_fr_BE:
                value['load_fr_BE'] = False
        if load_nl_BE or load_nl_NL:
            value['coa_lang'] = 'nl'
        elif load_fr_BE or load_fr_FR:
            value['coa_lang'] = 'fr'
        if value:
            res['value'] = value
        return res

    def copy_xlat(self, langs, in_field, in_recs, out_recs):
        # create ir.translation entries based upon
        # 1-1 relationship between in_ and out_ params
        cr = in_recs._cr
        in_ids = [x.id for x in in_recs]
        out_ids = [x.id for x in out_recs]
        if len(in_ids) != len(out_ids):
            _logger.error(
                "generate translations from template "
                "for %s failed (error 1)!", out_recs._name)
            raise Warning(
                _("The generation of translations from the template "
                  "for %s failed!"
                  "\nPlease report this issue via your Odoo support channel.")
                % out_recs._name)
        cr.execute(
            "SELECT id, " + in_field + " FROM " + in_recs._table +
            " WHERE id IN %s ORDER BY id", (tuple(in_ids),))
        sources = cr.fetchall()
        cr.execute(
            "SELECT id, " + in_field + " FROM " + out_recs._table +
            " WHERE id IN %s ORDER BY id", (tuple(out_ids),))
        sources_checks = cr.fetchall()
        for lang in langs:
            cr.execute(
                "SELECT res_id, src, value FROM ir_translation "
                "WHERE name=%s AND type='model' "
                "AND lang=%s AND res_id IN %s "
                "AND module=%s "
                "ORDER by res_id",
                (in_recs._name + ',' + in_field, lang, tuple(in_ids),
                 'l10n_be_coa_multilang'))
            xlats = cr.fetchall()
            if len(xlats) != len(filter(lambda x: x[1], sources)):
                _logger.warn(
                    "generate translations from template for %s failed "
                    "(template translations incomplete, lang = %s)!",
                    out_recs._name, lang)
            else:
                xi = 0
                for i, check in enumerate(sources_checks):
                    if sources[i][1]:
                        src = xlats[xi][1]
                        value = xlats[xi][2]
                        xi += 1
                        if check[1] != src:
                            _logger.error(
                                "generate translations from template "
                                "%s (id:%s) failed (error 3)!"
                                "\n%s,%s = '%s' i.s.o. '%s'.",
                                in_recs._name, xlats[xi][0], out_recs._name,
                                in_field, check, src)
                            raise Warning(
                                _("The generation of translations "
                                  "from the template for %s failed!"
                                  "\nPlease report this issue via your "
                                  "Odoo support channel.")
                                % out_recs._name)
                        in_recs.env['ir.translation'].create(
                            {'name': out_recs._name + ',' + in_field,
                             'type': 'model',
                             'res_id': out_recs[i].id,
                             'lang': lang,
                             'src': src,
                             'value': value,
                             'module': 'l10n_be_coa_multilang',
                             'state': 'translated'})

    def execute(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if context.get('next_action') == 'account.action_wizard_multi_chart':
            del context['next_action']
            del context['company_id']
        env = api.Environment(cr, uid, context)
        wiz = self.browse(cr, uid, ids[0])
        res = super(wizard_multi_charts_accounts, self).execute(
            cr, uid, ids, context={})
        if not wiz.multilang_be:
            return res

        if wiz.multilang_coa:
            to_install = env['ir.module.module'].search(
                [('name', '=', 'l10n_account_translate')])
            if not to_install:
                raise Warning(
                    _("Module 'l10n_account_translate' is not available "
                      "in the addons path. "
                      "\nPlease download this module from 'apps.odoo.com'.")
                    )
            else:
                to_install = to_install[0]
            if to_install.state != 'installed':
                self.pool['ir.module.module'].button_immediate_install(
                    cr, uid, [to_install.id],
                    context=context)

        # Update company country, this is required for auto-configuration
        # of the legal financial reportscheme.
        belgium = env['res.country'].search([('code', '=', 'BE')])[0]
        wiz.company_id.write({'country_id': belgium.id})

        chart_template = wiz.chart_template_id
        chart_template_root = chart_template

        chart_templates = [chart_template]
        parent_chart = chart_template.parent_id
        while parent_chart:
            chart_templates.insert(0, parent_chart)
            chart_template_root = parent_chart
            parent_chart = parent_chart.parent_id

        # load languages
        langs = (wiz.load_nl_BE and ['nl_BE'] or []) + \
            (wiz.load_fr_BE and ['fr_BE'] or []) + \
            (wiz.load_nl_NL and ['nl_NL'] or []) + \
            (wiz.load_fr_FR and ['fr_FR'] or [])

        if langs:
            installed_modules = env['ir.module.module'].search(
                [('state', '=', 'installed')])
            for lang in langs:
                lang_recs = env['res.lang'].search([('code', '=', lang)])
                if not lang_recs:
                    self.pool['ir.module.module'].update_translations(
                        cr, uid, [x.id for x in installed_modules], lang,
                        context=context)

        # find all installed fr/nl languages
        cr.execute(
            "SELECT code from res_lang "
            "WHERE code like 'fr_%' "
            "OR code like 'nl_%'")
        langs = cr.fetchall()
        langs = [x[0] for x in langs]

        # copy account.account translations
        in_field = 'name'
        acc_root = env['account.account'].search(
            [('company_id', '=', wiz.company_id.id),
             ('parent_id', '=', None)])[0]
        account_tmpls = env['account.account.template']
        for template in chart_templates:
            children_acc_criteria = [('chart_template_id', '=', template.id)]
            if template.account_root_id.id:
                children_acc_criteria = ['|'] + children_acc_criteria + \
                    ['&', ('parent_id', 'child_of',
                           [template.account_root_id.id]),
                     ('chart_template_id', '=', False)]
            account_tmpls += account_tmpls.search(
                [('nocreate', '!=', True)] +
                children_acc_criteria, order='id')
        account_tmpls = account_tmpls[1:]
        accounts = acc_root.search(
            [('id', 'child_of', [acc_root.id])], order='id')[1:]
        # remove accounts created outside the template copy process
        # (e.g. bank accounts)
        diff = len(accounts) - len(account_tmpls)
        if diff:
            accounts = accounts[:-diff]
        # Perform basic sanity check on in/out pairs to protect against
        # changes in the process that generates accounts from templates
        for i, tmpl in enumerate(account_tmpls):
            if tmpl.code != accounts[i].code:
                raise Warning(
                    _("The generation of translations from the template "
                      "for %s failed! \nPlease report this issue via "
                      "your Odoo support channel.")
                    % accounts._name)
        if not wiz.multilang_coa:
            lang = False
            if wiz.coa_lang == 'en':
                cr.execute(
                    "SELECT code from res_lang "
                    "WHERE code like 'en_%' LIMIT 1")
                lang = cr.fetchone()
                lang = lang and lang[0]
            elif wiz.coa_lang == 'nl':
                lang = (wiz.load_nl_BE and 'nl_BE') or \
                    (wiz.load_nl_NL and 'nl_NL')
                if not lang:
                    cr.execute(
                        "SELECT code from res_lang "
                        "WHERE code like 'nl_%' LIMIT 1")
                    lang = cr.fetchone()
                    lang = lang and lang[0]
            elif wiz.coa_lang == 'fr':
                lang = (wiz.load_fr_BE and 'fr_BE') or \
                    (wiz.load_fr_FR and 'fr_FR')
                if not lang:
                    cr.execute(
                        "SELECT code from res_lang "
                        "WHERE code like 'fr_%' LIMIT 1")
                    lang = cr.fetchone()
                    lang = lang and lang[0]
            if not lang:
                raise Warning(
                    _("The setup of the Accounts has failed since language "
                      "'%s' is not installed on your database.")
                    % wiz.coa_lang)
            account_tmpls = account_tmpls.with_context(lang=lang)
            for i, account in enumerate(accounts):
                account.name = account_tmpls[i].name
        else:
            self.copy_xlat(langs, in_field, account_tmpls, accounts)

        # copy account.tax.code translations
        in_field = 'name'
        tax_code_template_root = \
            chart_template_root.tax_code_root_id
        tax_code_root = env['account.tax.code'].with_context({}).search(
            [('company_id', '=', wiz.company_id.id),
             ('parent_id', '=', None)])[0]
        tax_code_tmpls = tax_code_template_root.search(
            [('id', 'child_of', [tax_code_template_root.id])],
            order='id')[1:]
        tax_codes = tax_code_root.search(
            [('id', 'child_of', [tax_code_root.id])], order='id')[1:]
        # Perform basic sanity check on in/out pairs to protect against
        # changes in the process that generates tax codes from templates
        for i, tmpl in enumerate(tax_code_tmpls):
            if tmpl.name != tax_codes[i].name:
                raise Warning(_(
                    "The generation of translations from the template "
                    "for %s failed! \nPlease report this issue via "
                    "your Odoo support channel.")
                    % tax_codes._name)
        self.copy_xlat(langs, in_field, tax_code_tmpls, tax_codes)

        # copy account.tax translations
        # skip xlats from templates in case tax rates (and hence naming)
        # can be modified via setup wizard
        if wiz.complete_tax_set:
            in_field = 'name'
            tax_tmpls = env['account.tax.template'].with_context({})
            for template in chart_templates:
                tax_tmpls += tax_tmpls.search(
                    [('chart_template_id', '=', template.id)], order='id'
                    )
            taxes = env['account.tax'].with_context({}).search(
                [('company_id', '=', wiz.company_id.id)], order='id'
                )
            # Perform basic sanity check on in/out pairs to protect against
            # changes in the process that generates tax objects from templates
            for i, tmpl in enumerate(tax_tmpls):
                if tmpl.name != taxes[i].name:
                    raise Warning(_(
                        "The generation of translations from the template "
                        "for %s failed! \nPlease report this issue via "
                        "your Odoo support channel.")
                        % taxes._name)
            self.copy_xlat(langs, in_field, tax_tmpls, taxes)

        # copy account.fiscal.position translations and note field
        fpos_tmpls = env['account.fiscal.position.template'].with_context({})
        for template in chart_templates:
            fpos_tmpls += fpos_tmpls.search(
                [('chart_template_id', '=', template.id)], order='id'
                )
        fpos = env['account.fiscal.position'].with_context({}).search(
            [('company_id', '=', wiz.company_id.id)], order='id'
            )
        # Perform basic sanity check on in/out pairs to protect against
        # changes in the process that generates tax objects from templates
        for i, tmpl in enumerate(fpos_tmpls):
            if tmpl.name != fpos[i].name:
                raise Warning(_(
                    "The generation of translations from the template "
                    "for %s failed! \nPlease report this issue via "
                    "your Odoo support channel.")
                    % fpos._name)
        for i, tmpl in enumerate(fpos_tmpls):
            if tmpl.note:
                fpos[i].note = tmpl.note
        in_fields = ['name', 'note']
        for in_field in in_fields:
            self.copy_xlat(langs, in_field, fpos_tmpls, fpos)

        # update the entries in the BNB/NBB legal report scheme
        upd_wiz = env['l10n_be.update_be_reportscheme']
        note = upd_wiz._update_be_reportscheme()
        if note:
            wiz = upd_wiz.create({'note': note})
            view = env.ref(
                'l10n_be_coa_multilang.update_be_reportscheme_result_view')
            return {
                'name': _('Results'),
                'res_id': wiz.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'l10n_be.update_be_reportscheme',
                'view_id': False,
                'target': 'new',
                'views': [(view.id, 'form')],
                'type': 'ir.actions.act_window'}

        if not res:
            menu = env.ref('base.menu_administration')
            res = {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menu.id}
            }

        return res
