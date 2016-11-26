# -*- coding: utf-8 -*-
# noqa: skip pep8 since code infra is correction of standard account module
# flake8: noqa
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class account_account(models.Model):
    """
    disable this _check_account_type constraint
    cf. https://github.com/odoo/odoo/pull/4512
    """
    _inherit = 'account.account'

    def _check_account_type(self, cr, uid, ids, context=None):
        """
        for account in self.browse(cr, uid, ids, context=context):
            if account.type in ('receivable', 'payable') and account.user_type.close_method != 'unreconciled':
                return False
        """
        return True

    _constraints = [
        # the constraint below has been disabled
        (_check_account_type, 'Configuration Error!\nYou cannot select an account type with a deferral method different of "Unreconciled" for accounts with internal type "Payable/Receivable".', ['user_type','type']),
    ]
