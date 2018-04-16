# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WizardMultiChartsAccounts(models.TransientModel):
    """
    - load nl & fr languages
    - update company_id country to Belgium
    """
    _inherit = 'wizard.multi.charts.accounts'

    load_nl_BE = fields.Boolean(string='Load Dutch (nl_BE) Translation')
    load_fr_BE = fields.Boolean(string='Load French (fr_BE) Translation')
    load_nl_NL = fields.Boolean(string='Load Dutch (nl_NL) Translation')
    load_fr_FR = fields.Boolean(string='Load French (fr_FR) Translation')
    l10n_be_coa_multilang = fields.Boolean(string='Multilingual Belgian CoA')
    monolang_coa = fields.Boolean(
        string='Monolingual Chart of Accounts',
        help="If checked, the General Account will become "
             "a monolingual field. \n"
             "This behaviour can be changed afterwards via "
             "Settings -> Configuration -> Accounting")
    coa_lang = fields.Selection(
        selection=[('en', 'English'),
                   ('fr', 'French'),
                   ('nl', 'Dutch')],
        string='Chart of Accounts Language',
        default=lambda self: self._default_coa_lang(),
        help="Select the language of the Chart Of Accounts")
    company_id = fields.Many2one(
        default=lambda self: self._default_company_id())

    @api.model
    def _default_coa_lang(self):
        res = self._context.get('lang')
        res = res and res[:2]
        return res in ['fr', 'nl'] and res or 'en'

    @api.model
    def _default_company_id(self):
        cid = self._context.get('company_id')
        if cid:
            return self.env['res.company'].browse(cid)
        else:
            return self.env.user.company_id

    @api.model
    def default_get(self, fields_list):
        """
        The standard default_get assumes that the user's default
        company is equal to the company selected in the settings
        but doesn't check which may give wrong results.
        We therefor have added this check here.
        """
        ctx = self._context.copy()
        if ctx.get('chart_company_id'):
            if ctx['chart_company_id'] != self.env.user.company_id.id:
                cpy = self.env['res.company'].browse(ctx['chart_company_id'])
                raise UserError(_(
                   "Your 'Current Company' must be set to '%s' !")
                   % cpy.name)
            ctx['default_company_id'] = ctx['chart_company_id']
            ctx['default_chart_template_id'] = ctx['chart_template_id']
        res = super(WizardMultiChartsAccounts,
                    self.with_context(ctx)).default_get(fields_list)
        if res.get('chart_template_id'):
            chart_template = self.env['account.chart.template'].browse(
                res['chart_template_id'])
            res['l10n_be_coa_multilang'] = chart_template.l10n_be_coa_multilang

        return res

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        self.l10n_be_coa_multilang = \
            self.chart_template_id.l10n_be_coa_multilang
        return super(WizardMultiChartsAccounts, self
                     ).onchange_chart_template_id()

    @api.onchange('load_nl_BE', 'load_fr_BE', 'load_nl_NL', 'load_fr_FR')
    def _onchange_load_lang(self):
        if self.load_nl_BE or self.load_fr_BE:
            self.load_nl_NL = False
            self.load_fr_FR = False
        elif self.load_nl_NL or self.load_fr_FR:
            self.load_nl_BE = False
            self.load_fr_BE = False
        if self.load_nl_BE or self.load_nl_NL:
            self.coa_lang = 'nl'
        elif self.load_fr_BE or self.load_fr_FR:
            self.coa_lang = 'fr'

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
        self_no_ctx = self.with_context({})
        res = super(
            WizardMultiChartsAccounts, self_no_ctx).execute()
        if not self.l10n_be_coa_multilang:
            return res

        if self.monolang_coa:
            to_install = self.env['ir.module.module'].search(
                [('name', '=', 'l10n_account_translate_off')])
            if not to_install:
                raise UserError(
                    _("Module 'l10n_account_translate_off' is not available "
                      "in the addons path. "
                      "\nPlease download this module from 'apps.odoo.com'.")
                    )
            if to_install.state != 'installed':
                to_install.button_immediate_install()

        # Update company country, this is required for auto-configuration
        # of the legal financial reportscheme.
        self.company_id.country_id = self.env.ref('base.be')

        chart_template = self.chart_template_id
        chart_templates = [chart_template]
        parent_chart = chart_template.parent_id
        while parent_chart:
            chart_templates.insert(0, parent_chart)
            parent_chart = parent_chart.parent_id

        # load languages
        langs = (self.load_nl_BE and ['nl_BE'] or []) + \
            (self.load_fr_BE and ['fr_BE'] or []) + \
            (self.load_nl_NL and ['nl_NL'] or []) + \
            (self.load_fr_FR and ['fr_FR'] or [])

        if langs:
            installed_modules = self.env['ir.module.module'].search(
                [('state', '=', 'installed')])
            for lang in langs:
                lang_rs = self.env['res.lang'].search([('code', '=', lang)])
                if not lang_rs:
                    installed_modules.update_translations(lang)

        # find all installed fr/nl languages
        lang_rs = self.env['res.lang'].search(
            ['|', ('code', '=like', 'fr_%'), ('code', '=like', 'nl_%')])
        langs = [l.code for l in lang_rs]

        # copy account.account translations
        in_field = 'name'
        account_tmpls = self_no_ctx.env['account.account.template']
        for template in chart_templates:
            account_tmpls += account_tmpls.search(
                [('chart_template_id', '=', template.id)])
        account_tmpls.sorted(key=lambda r: r.code)
        accounts = self_no_ctx.env['account.account'].search(
            [('company_id', '=', self.company_id.id)], order='code')

        # Remove accounts with no account_template counterpart.
        # The logic is based upon template codes with length equal
        # to acount.chart.template,code_digits which is the case
        # for the current 'l10n_be_coa_multilang' chart
        codes = [x.code for x in accounts]
        account_tmpls = account_tmpls.filtered(
            lambda r: r.code in codes)
        tmpl_codes = [x.code for x in account_tmpls]
        accounts = accounts.filtered(
            lambda r: r.code in tmpl_codes)
        if self.monolang_coa:
            lang = False
            if self.coa_lang == 'en':
                lang = self.env['res.lang'].search(
                    [('code', '=like', 'en_%')], limit=1).code
            elif self.coa_lang == 'nl':
                lang = (self.load_nl_BE and 'nl_BE') or \
                    (self.load_nl_NL and 'nl_NL')
                if not lang:
                    lang = self.env['res.lang'].search(
                        [('code', '=like', 'nl_%')], limit=1).code
            elif self.coa_lang == 'fr':
                lang = (self.load_fr_BE and 'fr_BE') or \
                    (self.load_fr_FR and 'fr_FR')
                if not lang:
                    lang = self.env['res.lang'].search(
                        [('code', '=like', 'fr_%')], limit=1).code
            if not lang:
                raise UserError(
                    _("The setup of the Accounts has failed since language "
                      "'%s' is not installed on your database.")
                    % self.coa_lang)
            account_tmpls = account_tmpls.with_context(lang=lang)
            for i, account in enumerate(accounts):
                account.name = account_tmpls[i].name
        else:
            self.copy_xlat(langs, in_field, account_tmpls, accounts)

        # copy account.tax codes and translations
        # skip xlats from templates in case tax rates (and hence naming)
        # can be modified via setup wizard
        if self.complete_tax_set:
            in_field = 'name'
            tax_tmpls = self_no_ctx.env['account.tax.template']
            for template in chart_templates:
                tax_tmpls += tax_tmpls.search(
                    [('chart_template_id', '=', template.id)],
                    order='sequence,description,name'
                    )
            taxes = self_no_ctx.env['account.tax'].search(
                [('company_id', '=', self.company_id.id)],
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
                taxes[i].code = tmpl.code
            self.copy_xlat(langs, in_field, tax_tmpls, taxes)

        # copy account.fiscal.position translations and note field
        fpos_tmpls = self_no_ctx.env[
            'account.fiscal.position.template'].with_context({})
        for template in chart_templates:
            fpos_tmpls += fpos_tmpls.search(
                [('chart_template_id', '=', template.id)], order='id'
                )
        fpos = self_no_ctx.env['account.fiscal.position'].search(
            [('company_id', '=', self.company_id.id)], order='id'
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

        ###### TODO #####
        """
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
        """

        if not res:
            menu = self.env.ref('base.menu_administration')
            res = {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menu.id}
            }

        return res
