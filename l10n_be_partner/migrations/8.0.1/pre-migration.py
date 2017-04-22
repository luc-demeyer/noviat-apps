# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        DELETE FROM ir_model_data
          WHERE module = 'l10n_be_partner'
          AND name in ('rptn_bv', 'rptn_ag', 'rptn_inc')
        """)
