# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
import openerp.addons.decimal_precision as dp


class AccountReinvoiceLine(models.Model):
    _name = 'account.reinvoice.line'
    _description = 'Reinvoice Line'

    move_line_in_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Origin', ondelete='cascade',
        readonly=True, index=True,
        help="Journal Item that triggered the creation "
             "of this line via it's Reinvoicing Key.")
    name = fields.Char(string='Name', readonly=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        required=True, readonly=True, index=True)
    journal_out_id = fields.Many2one(
        comodel_name='account.journal', string='Sales Journal',
        required=True, readonly=True, index=True)
    invoice_line_out_id = fields.Many2one(
        comodel_name='account.invoice.line', string='Outgoing Invoice Line',
        ondelete='set null',
        readonly=True, index=True)
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product',
        readonly=True, index=True)
    amount = fields.Float(
        string='Amount', digits=dp.get_precision('Account'), readonly=True)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True)

    @api.multi
    def unlink(self):
        """
        Remove also related reinvoice lines.
        Prevent unlink if out_invoices.
        """
        out_invoices = self.env['account.invoice']
        all_arls = self.env['account.reinvoice.line']
        for arl in self:
            dist_arls = arl.move_line_in_id.reinvoice_line_ids
            for dist_arl in dist_arls:
                if dist_arl not in all_arls:
                    all_arls += dist_arl
        for arl in dist_arls:
            out_invoice = arl.invoice_line_out_id.invoice_id
            if out_invoice not in out_invoices:
                out_invoices += out_invoice
        if out_invoices:
            inv_list = [
                ((x.type == 'out_invoice' and _("Invoice") or _("Refund"))
                 + " " + (x.number or ''),
                 x.id)
                for x in out_invoices]
            inv_list = ', '.join([
                "%s (id:%s)" % (x, y)
                for x, y in inv_list])
            raise UserError(_(
                "You cannot delete Reinvoice Lines "
                "linked to outgoing Invoices."
                "\nYou should first remove the following invoices:"
                "\n%s") % inv_list)
        return super(AccountReinvoiceLine, all_arls).unlink()
