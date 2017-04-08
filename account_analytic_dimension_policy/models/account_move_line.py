# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountMoveLine(models.Model):
    """
    This module adds fields to facilitate UI enforcement
    of analytic dimensions.
    """
    _inherit = 'account.move.line'

    analytic_dimension_policy = fields.Selection(
        string='Policy for analytic dimension',
        related='account_id.analytic_dimension_policy', readonly=True)
    move_state = fields.Selection(
        string='Move State',
        related='move_id.state',
        readonly=True)

    def fields_get(self, cr, uid, allfields=None, context=None,
                   write_access=True, attributes=None):
        """
        force 'move_state' into non-required field to allow creation of
        account.move.line objects via the standard 'Journal Items' menu entry
        """
        res = super(AccountMoveLine, self).fields_get(
            cr, uid, allfields=allfields, context=context,
            write_access=write_access, attributes=attributes)
        if res.get('move_state'):
            res['move_state']['required'] = False
        return res
