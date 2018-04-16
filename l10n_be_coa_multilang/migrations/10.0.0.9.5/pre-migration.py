# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def remove_data(cr, module, model):
    """
    remove trailing 'l10n_be' templates and xml ids.
    """
    cr.execute(
        "SELECT id, res_id FROM ir_model_data "
        "WHERE module=%s AND model=%s",
        (module, model))
    res = cr.fetchall()
    if res:
        res_ids = tuple([x[1] for x in res])
        table = model.replace('.', '_')
        query = "DELETE FROM %s WHERE id IN %%s" % table
        cr.execute(query, (res_ids,))
        imd_ids = tuple([x[0] for x in res])
        cr.execute(
            "DELETE from ir_model_data "
            "WHERE id IN %s", (imd_ids,))


def update_ir_model_data(cr, module, model):
    """
    Ensure that templates will be updated by module upgrade.
    """
    cr.execute(
        "SELECT id FROM ir_model_data "
        "WHERE module=%s AND model=%s AND noupdate=True",
        (module, model))
    res = cr.fetchall()
    if res:
        res_ids = tuple([x[0] for x in res])
        cr.execute(
            "UPDATE ir_model_data SET noupdate = False "
            "WHERE id IN %s", (res_ids,))


def migrate(cr, version):
    """
    l10n_be_coa_multilang installation fails if there are still
    some trailing account templates from l10n_be.
    We therefor need to remove those first.
    """
    module = 'l10n_be'
    # check l10n_be status
    # (V6 version of l10n_be_coa_multilang had l10n_be dependenct)
    cr.execute(
        "SELECT state FROM ir_module_module "
        "WHERE name = %s and state = 'installed'",
        (module,))
    res = cr.fetchone()
    if res:
        raise UserError(
            "Installation of module 'l10n_be_coa_multilang failed.\n"
            "You need uninstall '%s' first" % module)

    # check if there are still some trailing account templates
    # from l10n_be and delete them.
    models = [
        'account.tax.code.template',
        'account.fiscal.position.tax.template',
        'account.fiscal.position.account.template',
        'account.fiscal.position.template',
        'account.tax.template',
        'account.account.template',
        'account.chart.template',
    ]
    for model in models:
        remove_data(cr, module, model)

    module = 'l10n_be_coa_multilang'
    for model in models:
        update_ir_model_data(cr, module, model)

    # make old account_tax_template names unique
    model = 'account.tax.template'
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module=%s AND model=%s",
        (module, model))
    res = cr.fetchall()
    att_ids = [x[0] for x in res]
    cr.execute(
        "UPDATE account_tax_template "
        "SET name = to_char(id, 'FM999') "
        "WHERE id IN %s",
        (tuple(att_ids),))

    # add transfer_account_id to account_chart_template
    name = 'aatn_580000'
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module=%s AND name=%s",
        (module, name))
    res = cr.fetchone()
    aatn_580000_id = res and res[0]
    name = 'l10n_be_coa_multilang_template'
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = %s AND name = %s",
        (module, name))
    res = cr.fetchone()
    chart_id = res and res[0]
    cr.execute(
        "UPDATE account_chart_template "
        "SET transfer_account_id=%s "
        "WHERE id=%s",
        (aatn_580000_id, chart_id))

    # remove old be_legal_financial_reportscheme entries
    model = 'be.legal.financial.reportscheme'
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module=%s AND model=%s",
        (module, model))
    res = cr.fetchall()
    scheme_ids = [x[0] for x in res]
    cr.execute(
        "DELETE FROM be_legal_financial_reportscheme "
        "WHERE id IN %s",
        (tuple(scheme_ids),))

    # remove old setup wizard view
    model = 'ir.ui.view'
    name = 'view_wizard_multi_chart_belgian_coa'
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module=%s AND model=%s AND name=%s",
        (module, model, name))
    res = cr.fetchone()
    view_id = res and res[0]
    cr.execute(
        "DELETE FROM ir_ui_view "
        "WHERE id = %s",
        (view_id,))
