# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def unlink(self):
        for tax in self:
            products = self.env['product.template'].with_context(
                active_test=False).search(
                    ['|', ('supplier_taxes_id', '=', tax.id),
                     ('taxes_id', '=', tax.id)])
            if products:
                product_list = [
                    '%s' % x.name for x in products]
                raise UserError(_(
                    "You cannot delete a tax that "
                    "has been set on product records"
                    "\nAs an alterative, you can disable a "
                    "tax via the 'active' flag."
                    "\n\nProduct records: %s") % product_list)
        return super(AccountTax, self).unlink()
