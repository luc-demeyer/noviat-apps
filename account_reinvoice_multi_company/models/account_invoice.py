# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from sys import exc_info
from traceback import format_exception

from openerp import api, fields, models, _
from openerp.exceptions import AccessError, Warning as UserError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    intercompany_invoice_id = fields.Integer(
        # Integer in stead of M2O to avoid access errors
        string='Intercompany Invoice Id', readonly=True,
        help="Incoming invoice Id in Customer's Company.")
    intercompany_invoice = fields.Boolean(
        string='Intercompany Invoice', store=True, index=True,
        compute='_compute_intercompany_invoice',
        help="This flag is set when this invoice "
             "is an Intercompany Invoice.")
    intercompany_invoice_ref = fields.Char(
        string='Intercompany Invoice',
        compute='_compute_intercompany_invoice_ref',
        help="Incoming invoice in Customer's Company.")

    @api.one
    @api.depends('intercompany_invoice_id')
    def _compute_intercompany_invoice(self):
        if self.intercompany_invoice_id:
            self.intercompany_invoice = True
        else:
            self.intercompany_invoice = False

    @api.one
    def _compute_intercompany_invoice_ref(self):
        if self.intercompany_invoice_id:
            ico_inv = self.sudo()._get_intercompany_invoice()
            if ico_inv:
                state_selection = self.fields_get(
                    allfields='state')['state']['selection']
                state_ui = filter(
                    lambda x: x[0] == ico_inv.state, state_selection)[0][1]
                ref = ico_inv.display_name + '(' + _("State") + ': ' \
                    + state_ui + ')'
                self.intercompany_invoice_ref = ref
        else:
            self.intercompany_invoice_ref = False

    @api.multi
    def unlink(self):
        for inv in self:
            ico_inv = inv._get_intercompany_invoice()
            if ico_inv:
                ico_inv.write({'intercompany_invoice_id': False})
        return super(AccountInvoice, self).unlink()

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for inv in self:
            if inv.type in ('out_invoice', 'out_refund'):
                ico_inv = inv.sudo()._get_intercompany_invoice()
                if ico_inv and ico_inv.state != 'cancel':
                    raise UserError(_(
                        "You can only cancel an intercompany invoice "
                        "if the associated Supplier Invoice in the "
                        "target company has been set to state 'Cancel'."))
        return res

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for inv in self:
            if inv.partner_id.intercompany_invoice \
                    and inv.type in ('out_invoice', 'out_refund'):
                err_msg = self._create_intercompany_invoice(inv)
                if err_msg:
                    raise UserError(err_msg)
        return res

    def _get_intercompany_invoice(self):
        ico_inv = False
        if self.intercompany_invoice_id:
            ico_inv = self.sudo().browse(self.intercompany_invoice_id)
        return ico_inv

    def _intercompany_invoice_error(self, out_invoice, err):
        err_msg = _("Creation of Incoming Invoice in Customer's Company "
                    "failed for invoice '%s'.") % out_invoice.number
        err_msg += '\n\n%s' % err
        _logger.error(err_msg)
        return err_msg

    def _prepare_intercompany_invoice_line_vals(
            self, out_invoice, line, target_company, target_user,
            target_partner, inv_type):
        # only company currency supported at this point in time
        curr = target_company.currency_id
        err = ''
        product = line.product_id
        inv_line_vals = {
            'product_id': product.id,
            'quantity': line.quantity,
            'price_unit': line.price_unit,
        }
        if product:
            try:
                p_change = self.env['account.invoice.line'].sudo(target_user).\
                    product_id_change(
                    product.id, line.uos_id.id, line.quantity, line.name,
                    inv_type, partner_id=target_partner.id,
                    fposition_id=target_partner.property_account_position.id,
                    price_unit=line.price_unit, currency_id=curr.id,
                    company_id=target_company.id)

            except AccessError, e:
                err = ', '.join([e.name, e.value])
                pref = "%s (id:%s)" % (product.name, product.id)
                err += '\n\n'
                err += _("Please ensure that Product '%s' "
                         "is available for users in Company '%s'."
                         ) % (pref, target_company.name)
                err = self._intercompany_invoice_error(out_invoice, err)

            except:
                err = _("Unknown Error")
                tb = ''.join(format_exception(*exc_info()))
                err += '\n\n' + tb
                err = self._intercompany_invoice_error(out_invoice, err)

            if not err:
                inv_line_vals.update(p_change['value'])
                inv_line_vals['invoice_line_tax_id'] = [
                    (6, 0, inv_line_vals['invoice_line_tax_id'])]
        else:
            # if no product -> get default account.
            acc = self.env['account.invoice.line']._default_account()
            if not acc:
                acc = self.env['ir.property'].get(
                    'property_account_expense_categ', 'product.category')
            if not acc:
                err = _(
                    "Creation of invoice line in target company failed."
                    "\nPlease use shared product records on outgoing "
                    "invoice lines. As an alternative you can define a "
                    "default expense account by defining a generic "
                    "'property_account_expense_categ' in the target company.")
            else:
                inv_line_vals['account_id'] = acc.id
        inv_line_vals['name'] = line.name
        return inv_line_vals, err

    def _get_intercompany_invoice_journal(self, out_invoice,
                                          target_company, inv_type):
        """
        Use this method to customize the selection of the
        incoming invoice journal.
        """
        j_type = inv_type == 'in_invoice' and 'purchase' or 'purchase_refund'
        domain = [
            ('company_id', '=', target_company.id),
            ('type', '=', j_type)]
        journals = self.env['account.journal'].search(domain)
        if not journals:
            err = _("No Journal of type '%s' defined in Company '%s'"
                    ) % (inv_type, target_company.name)
            err_msg = self._intercompany_invoice_error(out_invoice, err)
            raise UserError(err_msg)
        mapping = self.env[
            'account.reinvoice.journal.mapping.multi.company'].sudo().search(
            [('company_id', '=', out_invoice.company_id.id),
             ('target_company', '=', str(target_company.id))])
        mapping = mapping.filtered(
            lambda r: out_invoice.journal_id.id in r.journal_out_ids._ids)
        if mapping and len(mapping) == 1:
            if j_type == 'purchase':
                journal_id = mapping.target_journal.id
            else:
                journal_id = mapping.target_refund_journal.id
            journal = self.env['account.journal'].browse(journal_id)
        else:
            journal = journals[0]
        return journal

    def _prepare_intercompany_invoice_vals(self, out_invoice,
                                           target_company, target_user):
        err = ''
        if out_invoice.type == 'out_invoice':
            inv_type = 'in_invoice'
        else:
            inv_type = 'in_refund'
        target_journal = self.env['account.invoice'].sudo(target_user).\
            _get_intercompany_invoice_journal(out_invoice,
                                              target_company, inv_type)
        target_currency = self.env['res.currency'].sudo(target_user).search(
            [('name', '=', out_invoice.currency_id.name),
             '|', ('company_id', '=', target_company.id),
             ('company_id', '=', False)])
        if not target_currency:
            raise UserError(_(
                "Currency error: \n"
                "Currency '%s' in not defined in Company '%s'.")
                % (out_invoice.currency_id.name, target_company.name))
        if len(target_currency) > 1:
            raise UserError(_(
                "Currency error: \n"
                "Currency '%s' defined multiple times in Company '%s' "
                "for user '%s")
                % (out_invoice.currency_id.name, target_company.name,
                   target_user.name))
        target_partner = out_invoice.company_id.partner_id.sudo(target_user)
        account = target_partner.property_account_payable
        fpos = target_partner.property_account_position
        inv_vals = {
            'name': out_invoice.name,
            'date_invoice': out_invoice.date_invoice,
            'intercompany_invoice_id': out_invoice.id,
            'partner_id': target_partner.id,
            'user_id': target_user.id,
            'journal_id': target_journal.id,
            'type': inv_type,
            'account_id': account.id,
            'company_id': target_company.id,
            'currency_id': target_currency.id,
        }
        if fpos:
            inv_vals['fiscal_position'] = fpos.id
        line_vals = []
        for line in out_invoice.invoice_line:
            tline, tline_err = self._prepare_intercompany_invoice_line_vals(
                out_invoice, line, target_company, target_user,
                target_partner, inv_type)
            if tline_err:
                if err:
                    err += '\n\n'
                err += tline_err
            else:
                line_vals.append(tline)
        inv_vals['invoice_line'] = [(0, 0, x) for x in line_vals]
        return inv_vals, err

    def _create_intercompany_invoice(self, out_invoice):
        ic_invoice = err_msg = False
        target_company = self.env['res.company'].sudo().search(
            [('partner_id', '=', out_invoice.partner_id.id)])
        target_user = out_invoice.partner_id.intercompany_invoice_user_id
        if target_user:
            tu_sudo = target_user.sudo(target_user)
            if tu_sudo.company_id != target_company:
                raise UserError(_(
                    "Configuration Error : "
                    "\nIntercompany User '%s' should belong to Company '%s'.")
                    % (tu_sudo.name, target_company.name))
            ctx = dict(self._context,
                       force_company=target_company.id,
                       intercompany_invoice=True)
            ic_inv_vals, err = self.with_context(ctx).sudo()\
                ._prepare_intercompany_invoice_vals(
                out_invoice, target_company, target_user)
            if not err:
                ic_invoice = self.env['account.invoice'].with_context(ctx)\
                    .sudo(target_user).create(ic_inv_vals)
                ic_invoice.button_reset_taxes()
                self.write({'intercompany_invoice_id': ic_invoice.id})
            else:
                err_msg = self._intercompany_invoice_error(out_invoice, err)
        else:
            err = "'Intercompany Invoice User' has not been defined."
            err_msg = self._intercompany_invoice_error(out_invoice, err)
        return err_msg
