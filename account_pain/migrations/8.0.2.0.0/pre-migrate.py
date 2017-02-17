# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        "SELECT res_id from ir_model_data "
        "WHERE module = 'account_pain' "
        "AND name = 'view_payment_order_form_inherit'")
    res = cr.fetchone()
    if res:
        cr.execute(
            "DELETE from ir_ui_view WHERE id = %s" % res[0])
