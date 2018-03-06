# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

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
        if len(in_recs) != len(out_recs):
            _logger.error(
                "The generation of translations from template "
                "for %s failed (error 1)!", out_recs._name)
            raise UserError(
                _("The generation of translations from the template "
                  "for %s failed!"
                  "\nPlease report this issue via your Odoo support channel.")
                % out_recs._name)

        for lang in langs:
            for i, in_rec in enumerate(in_recs):
                out_rec = out_recs[i]
                if getattr(in_rec, in_field) != getattr(out_rec, in_field):
                    _logger.error(
                        "generate translations from template "
                        "%s (id:%s) failed (error 3)!"
                        "\n%s,%s = '%s' i.s.o. '%s'.",
                        in_rec._name, in_rec.id, out_rec._name, in_field,
                        getattr(out_rec, in_field), getattr(in_rec, in_field))
                    raise UserError(
                        _("The generation of translations "
                          "from the template for %s failed!"
                          "\nPlease report this issue via your "
                          "Odoo support channel.")
                        % out_rec._name)
                value = in_rec.with_context({'lang': lang}).read(
                    [in_field])[0][in_field]
                if value:
                    out_rec.with_context({'lang': lang}).write(
                        {in_field: value})

    @api.multi
    def execute(self):
        context = self._context.copy()
        cr = self._cr
        uid = self._uid
        if context.get('next_action') == 'account.action_wizard_multi_chart':
            del context['next_action']
            del context['company_id']
        wiz = self[0]
        res = super(
            wizard_multi_charts_accounts, self.with_context({})).execute()
        if not wiz.multilang_be:
            return res

        if wiz.multilang_coa:
            to_install = self.env['ir.module.module'].search(
                [('name', '=', 'l10n_account_translate')])
            if not to_install:
                raise UserError(
                    _("Module 'l10n_account_translate' is not available "
                      "in the addons path. "
                      "\nPlease download this module from 'apps.odoo.com'.")
                )
            if to_install.state != 'installed':
                to_install.button_immediate_install()

        env_no_ctx = api.Environment(cr, uid, {})

        # Update company country, this is required for auto-configuration
        # of the legal financial reportscheme.
        belgium = self.env['res.country'].search([('code', '=', 'BE')])[0]
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
            installed_modules = self.env['ir.module.module'].search(
                [('state', '=', 'installed')])
            for lang in langs:
                lang_recs = self.env['res.lang'].search([('code', '=', lang)])
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
        acc_root = env_no_ctx['account.account'].search(
            [('company_id', '=', wiz.company_id.id),
             ('parent_id', '=', None)])[0]
        account_tmpls = env_no_ctx['account.account.template']
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
                raise UserError(
                    _("The generation of translations from the template "
                      "for %s failed! "
                      "\nAccount Template : %s, Account: %s"
                      "\nPlease report this issue via "
                      "your Odoo support channel.")
                    % (accounts._name, tmpl.code, accounts[i].code))
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
                raise UserError(
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
            chart_template_root.tax_code_root_id.with_context({})
        tax_code_root = env_no_ctx['account.tax.code'].search(
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
                raise UserError(_(
                    "The generation of translations from the template "
                    "for %s failed! "
                    "\nTax Code Template : %s, Tax Code: %s"
                    "\nPlease report this issue via "
                    "your Odoo support channel.")
                    % (tax_codes._name, tmpl.name, tax_codes[i].name))
        self.copy_xlat(langs, in_field, tax_code_tmpls, tax_codes)

        # copy account.tax translations
        # skip xlats from templates in case tax rates (and hence naming)
        # can be modified via setup wizard
        if wiz.complete_tax_set:
            in_field = 'name'
            tax_tmpls = env_no_ctx['account.tax.template']
            for template in chart_templates:
                tax_tmpls += tax_tmpls.search(
                    [('chart_template_id', '=', template.id)],
                    order='sequence,description,name'
                )
            taxes = env_no_ctx['account.tax'].search(
                [('company_id', '=', wiz.company_id.id)],
                order='sequence,description,name'
            )
            # Perform basic sanity check on in/out pairs to protect against
            # changes in the process that generates tax objects from templates
            for i, tmpl in enumerate(tax_tmpls):
                if tmpl.name != taxes[i].name:
                    raise UserError(_(
                        "The generation of translations from the template "
                        "for %s failed! "
                        "\nTax Template : %s, Tax: %s"
                        "\nPlease report this issue via "
                        "your Odoo support channel.")
                        % (taxes._name, tmpl.name, taxes[i].name))
            self.copy_xlat(langs, in_field, tax_tmpls, taxes)

        # copy account.fiscal.position translations and note field
        fpos_tmpls = self.env[
            'account.fiscal.position.template'].with_context({})
        for template in chart_templates:
            fpos_tmpls += fpos_tmpls.search(
                [('chart_template_id', '=', template.id)], order='id'
            )
        fpos = env_no_ctx['account.fiscal.position'].search(
            [('company_id', '=', wiz.company_id.id)], order='id'
        )
        # Perform basic sanity check on in/out pairs to protect against
        # changes in the process that generates tax objects from templates
        for i, tmpl in enumerate(fpos_tmpls):
            if tmpl.name != fpos[i].name:
                raise UserError(_(
                    "The generation of translations from the template "
                    "for %s failed! "
                    "\nFiscal Position Template : %s, Fiscal Position: %s"
                    "\nPlease report this issue via "
                    "your Odoo support channel.")
                    % (fpos._name, tmpl.name, fpos[i].name))
        for i, tmpl in enumerate(fpos_tmpls):
            if tmpl.note:
                fpos[i].note = tmpl.note
        in_fields = ['name', 'note']
        for in_field in in_fields:
            self.copy_xlat(langs, in_field, fpos_tmpls, fpos)

        # update the entries in the BNB/NBB legal report scheme
        upd_wiz = self.env['l10n_be.update_be_reportscheme']
        note = upd_wiz._update_be_reportscheme()
        if note:
            wiz = upd_wiz.create({'note': note})
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = 'l10n_be_update_be_reportscheme_view_form_result'
            view = self.env.ref('%s.%s' % (module, result_view))
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
            menu = self.env.ref('base.menu_administration')
            res = {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menu.id}
            }

        return res
