# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nBeCoaMultilangConfig(models.TransientModel):
    """
    - load nl & fr languages
    - update company_id country to Belgium
    """
    _inherit = 'res.config'
    _name = 'l10n.be.coa.multilang.config'

    load_nl_BE = fields.Boolean(string='Load Dutch (nl_BE) Translation')
    load_fr_BE = fields.Boolean(string='Load French (fr_BE) Translation')
    load_nl_NL = fields.Boolean(string='Load Dutch (nl_NL) Translation')
    load_fr_FR = fields.Boolean(string='Load French (fr_FR) Translation')
    monolang_coa = fields.Boolean(
        string='Monolingual Chart of Accounts',
        default=lambda self: self._default_coa_lang(),
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
        comodel_name='res.company', string='Company',
        required=True)

    @api.model
    def _default_monolang_coa(self):
        # TODO: review logic based upon actual setting of
        # account.account,name translate flag
        name = 'l10n_account_translate_off'
        module = self.env['ir.module.module'].search(
            ['name', '=', name])
        if not module:
            raise UserError(_(
                "Module '%s' is not available "
                "in the addons path. "
                "\nPlease download this module from 'apps.odoo.com'."
            ) % name)
        if module.state == 'installed':
            return True

    @api.model
    def _default_coa_lang(self):
        res = self.env.context.get('lang')
        res = res and res[:2]
        return res in ['fr', 'nl'] and res or 'en'

    @api.model
    def default_get(self, fields_list):
        ctx = self.env.context.copy()
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'account.config.settings':
            acc_config_wiz = self.env[active_model].browse(active_id)
            ctx['default_company_id'] = acc_config_wiz.company_id.id
        elif not ctx.get('default_company_id'):
            ctx['default_company_id'] = self.env.user.company_id.id
        return super(L10nBeCoaMultilangConfig,
                     self.with_context(ctx)).default_get(fields_list)

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

    def copy_xlat(self, langs, in_field, in_recs, out_recs,
                  field_check=True):
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
                if field_check and (getattr(in_rec, in_field)
                                    != getattr(out_rec, in_field)):
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

        if self.monolang_coa:
            to_install = self.env['ir.module.module'].search(
                [('name', '=', 'l10n_account_translate_off')])
            if to_install.state != 'installed':
                to_install.button_immediate_install()
        else:
            to_install = self.env['ir.module.module'].search(
                [('name', '=', 'l10n_multilang')])
            if to_install.state != 'installed':
                to_install.button_immediate_install()
            to_uninstall = self.env['ir.module.module'].search(
                [('name', '=', 'l10n_account_translate_off')])
            if to_uninstall.state == 'installed':
                to_uninstall.button_immediate_uninstall()

        # Update company country, this is required for auto-configuration
        # of the legal financial reportscheme.
        self.company_id.country_id = self.env.ref('base.be')

        module = __name__.split('addons.')[1].split('.')[0]
        chart_template = self.env.ref(
            '%s.l10n_be_coa_multilang_template' % module)
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
        codes = accounts.mapped('code')
        account_tmpls = account_tmpls.filtered(
            lambda r: r.code in codes)
        tmpl_codes = account_tmpls.mapped('code')
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
            for i, account in enumerate(accounts):
                account.name = account_tmpls[i].name
            # no field value check to enable mono- to multi-lang
            # via this config wizard
            self.copy_xlat(langs, in_field, account_tmpls, accounts,
                           field_check=False)

        # copy account.tax codes and translations
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
        in_fields = ['name', 'description']
        for in_field in in_fields:
            self.copy_xlat(langs, in_field, tax_tmpls, taxes,
                           field_check=False)

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
            self.copy_xlat(langs, in_field, fpos_tmpls, fpos,
                           field_check=False)

        # update the entries in the BNB/NBB legal report scheme
        upd_wiz = self.env['l10n_be.update_be_reportscheme']
        upd_ctx = {'l10n.be.coa.multilang.config': 1}
        note = upd_wiz.with_context(upd_ctx)._update_be_reportscheme()
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
                'type': 'ir.actions.act_window',
            }
        else:
            return {}
