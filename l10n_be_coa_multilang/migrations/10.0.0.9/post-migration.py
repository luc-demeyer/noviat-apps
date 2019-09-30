# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def migrate(cr, version):
    """
    Update account_tax_names.
    """
    cr.execute(
        "SELECT id, description, name FROM account_tax "
        "WHERE description LIKE 'VAT-%' "
        "ORDER BY sequence DESC")
    at_codes = cr.fetchall()
    for at_id, at_code, at_name in at_codes:
        imd_name = 'attn_%s' % at_code
        imd_name = imd_name.replace('-L', '-G')
        cr.execute(
            "SELECT res_id FROM ir_model_data "
            "WHERE module = 'l10n_be_coa_multilang' "
            "AND model = 'account.tax.template' "
            "AND name = %s",
            (imd_name,))
        res_id = cr.fetchone()
        if res_id:
            cr.execute(
                "SELECT att.name FROM account_tax_template att "
                "WHERE id = %s",
                (res_id[0],))
            att_name = cr.fetchone()[0]
        else:
            continue
        if att_name != at_name:
            _logger.warn(
                "updating account.tax,%s with name '%s'",
                at_id, att_name)
            try:
                with cr.savepoint():
                    cr.execute(
                        "UPDATE account_tax SET name = %s "
                        "WHERE id = %s", (att_name, at_id))
            except Exception:
                _logger.error(
                    "Update of account.tax,%s with name '%s' failed.",
                    at_id, att_name)
