# -*- coding: utf-8 -*-
# Copyright 2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """
    Remove be.legal.financial.reportscheme for account_group 499.
    This entry will be recreated by the module data/
    """
    cr.execute(
        "DELETE FROM be_legal_financial_reportscheme "
        "WHERE account_group = '499'")
