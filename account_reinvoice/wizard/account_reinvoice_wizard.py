# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time

from openerp import api, fields, models, registry, _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountReinvoiceWizard(models.TransientModel):
    _name = 'account.reinvoice.wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    journal_in_ids = fields.Many2many(
        comodel_name='account.journal', string='Input Journals',
        domain=[('type', 'not in', ['sale', 'sale_refund', 'situation'])],
        help="Leave empty to select all journals")
    date_invoice = fields.Date(
        string='Invoice Date',
        help="Keep empty to use the current date")
    period_id = fields.Many2one(
        comodel_name='account.period', string='Force Period',
        domain=[('state', '=', 'draft'), ('special', '=', False)])
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Sales Journal',
        default=lambda self: self._default_journal_id(),
        domain=[('type', '=', 'sale')], required=True)
    refund_journal_id = fields.Many2one(
        comodel_name='account.journal', string='Sales Refund Journal',
        default=lambda self: self._default_refund_journal_id(),
        domain=[('type', '=', 'sale_refund')], required=True)
    income_account_id = fields.Many2one(
        comodel_name='account.account', string='Default Income Account',
        help="Default Income Account. This value will be used for those "
             "outgoing invoice lines where the Income Account can not "
             "be retrieved via the Product Record configuration.")
    uninvoiced = fields.Boolean(
        string='Uninvoiced', default=True,
        help="Include pending uninvoiced Reinvoice Lines.")
    reinvoice_key_ids = fields.Many2many(
        comodel_name='account.reinvoice.key', string='Reinvoice Keys',
        column1='wiz_id', column2='key_id',
        help="Leave empty to select all journals")
    note = fields.Text(string='Notes')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', readonly=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account.reinvoice.wizard'))

    @api.model
    def _default_journal_id(self):
        company_id = self.env['res.company']._company_default_get(
            'account.reinvoice.wizard')
        domain = [
            ('company_id', '=', company_id),
            ('type', '=', 'sale')]
        journals = self.env['account.journal'].search(domain)
        if len(journals) == 1:
            return journals[0]
        else:
            return False

    @api.model
    def _default_refund_journal_id(self):
        company_id = self.env['res.company']._company_default_get(
            'account.reinvoice.wizard')
        domain = [
            ('company_id', '=', company_id),
            ('type', '=', 'sale_refund')]
        journals = self.env['account.journal'].search(domain)
        if len(journals) == 1:
            return journals[0]
        else:
            return False

    @api.onchange('journal_in_ids')
    def _onchange_journal_in_ids(self):
        if self.journal_in_ids:
            mapping = self.env['account.reinvoice.journal.mapping'].search(
                [('company_id', '=', self.company_id.id),
                 ('journal_in_ids', 'in', self.journal_in_ids.ids)])
            if mapping and len(mapping) == 1:
                self.journal_id = mapping.journal_id
                self.refund_journal_id = mapping.refund_journal_id

    @api.one
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if self.date_from:
            date_to = self.date_to or fields.Date.today()
            if date_to < self.date_from:
                raise ValidationError(
                    _("The 'Date From' must precede the 'Date To'."))

    def _hashcode_field_dict(self, arl):
        hc_field_dict = {
            'name': arl.name or False,
            'product_id': arl.product_id.id or False,
            'partner_id': arl.partner_id.id or False,
            'journal_out_id': arl.journal_out_id.id or False,
        }
        return hc_field_dict

    def _hashcode_field_list(self):
        always = ['partner_id', 'journal_out_id']
        # TODO: get 'extra' list from company dependent config screen
        extra = ['product_id']
        return always + extra

    def _reinvoice_line_hashcode(self, arl):
        hc_list = self._hashcode_field_list()
        hc_dict = self._hashcode_field_dict(arl)
        hashcode = '-'.join([unicode(hc_dict[f]) for f in hc_list])
        return hashcode

    def _reinvoice_line_fields_to_sum(self):
        return ['price_unit']

    def _prepare_out_invoice_line_vals(self, arl):
        sign = arl.journal_out_id.type == 'sale' and 1 or -1
        inv_line_vals = {
            'name': arl.name,
            'product_id': arl.product_id.id,
            'price_unit': sign * arl.amount,
            'reinvoice_line_ids': [(6, 0, [arl.id])]
        }
        return inv_line_vals

    def _finalize_out_invoice_line_vals(self, line_vals, partner, journal):
        fpos = partner.property_account_position
        product = self.env['product.product'].browse(
            line_vals.get('product_id'))
        account = product.property_account_income \
            or product.categ_id.property_account_income_categ \
            or self.income_account_id
        if account:
            account = fpos.map_account(account)
            line_vals['account_id'] = account.id
        taxes = product.taxes_id or account.tax_ids
        fp_taxes = fpos.map_tax(taxes)
        line_vals['invoice_line_tax_id'] = [(6, 0, fp_taxes.ids)]

    def _prepare_out_invoice_vals(self, partner, journal):
        inv_vals = {
            'partner_id': partner.id,
            'journal_id': journal.id,
            # only company currency supported at this point in time
            'currency_id': journal.company_id.currency_id.id,
            'type': journal.type == 'sale' and 'out_invoice' or 'out_refund',
            'account_id': partner.property_account_receivable.id,
            'company_id': self.company_id.id,
        }
        return inv_vals

    def _finalize_out_invoice_vals(self, inv_vals):
        """
        Placeholder for custom modules
        """
        pass

    def _group_reinvoice_lines(self, reinvoice_lines):
        grouped = {}
        fields_to_sum = self._reinvoice_line_fields_to_sum()
        for arl in reinvoice_lines:
            line_vals = self._prepare_out_invoice_line_vals(arl)
            hc = self._reinvoice_line_hashcode(arl)
            if hc in grouped:
                rls = line_vals['reinvoice_line_ids']
                assert len(rls) == 1, "Programming Error"
                rl = rls[0]
                assert rl[0] == 6, "Programming Error"
                arl_ids = rl[2]
                del line_vals['reinvoice_line_ids']
                grouped[hc][0]['reinvoice_line_ids'][0][2].extend(arl_ids)
                for field in fields_to_sum:
                    grouped[hc][0][field] += line_vals[field]
            else:
                grouped[hc] = [line_vals, arl.partner_id, arl.journal_out_id]
        return grouped

    def _create_invoices(self, reinvoice_lines):
        date_invoice = self.date_invoice or fields.Date.today()
        grouped = self._group_reinvoice_lines(reinvoice_lines)
        out_invoice_ids = []
        out_refund_ids = []
        invoices = {}
        for group in grouped:
            line_vals, partner, journal = grouped[group]
            k = '%s-%s' % (partner.id, journal.id)
            if k in invoices:
                self._finalize_out_invoice_line_vals(
                    line_vals, partner, journal)
                invoices[k]['invoice_line'].append(
                    (0, 0, line_vals))
            else:
                inv_vals = self._prepare_out_invoice_vals(partner, journal)
                if self.date_invoice:
                    inv_vals['date_invoice'] = date_invoice
                if self.period_id:
                    inv_vals['period_id'] = self.period_id.id
                self._finalize_out_invoice_line_vals(
                    line_vals, partner, journal)
                inv_vals['invoice_line'] = [(0, 0, line_vals)]
                invoices[k] = inv_vals

        for k in invoices:
            inv_vals = invoices[k]
            self._finalize_out_invoice_vals(inv_vals)
            # For some reason the ORM shows non-linear performance
            # when creating multiple invoices in the same Environment.
            # We bypass this by using a new Environment per create.
            # As a side-effect the code infra also ensures a commit
            # per create, hence work performed in large reinvoice
            # batches will be saved when the reinvoice job gets killed
            # for whatever reason.
            with api.Environment.manage():
                with registry(self.env.cr.dbname).cursor() as new_cr:
                    new_env = api.Environment(
                        new_cr, self.env.uid, self.env.context)
                    time_start = time.time()
                    inv = new_env['account.invoice'].create(inv_vals)
                    time_end = time.time() - time_start
                    _logger.warn(
                        'invoice %s create processing time = %.3f seconds',
                        k, time_end)
                    if inv.type == 'out_invoice':
                        out_invoice_ids.append(inv.id)
                    else:
                        out_refund_ids.append(inv.id)

        return out_invoice_ids, out_refund_ids

    def _prepare_reinvoice_line_vals(self, aml, dist_entry):
        sign = aml.debit > 0 and 1 or -1
        amount = sign * (aml.debit or aml.credit) * dist_entry.rate / 100
        if sign == 1:
            journal = self.journal_id
        else:
            journal = self.refund_journal_id
        vals = {
            'move_line_in_id': aml.id,
            'name': aml.name,
            'partner_id': dist_entry.partner_id.id,
            'product_id': aml.product_id.id,
            'amount': amount,
            'journal_out_id': journal.id,
            'company_id': self.company_id.id,
        }
        return vals

    def _create_reinvoice_line(self, aml, dist_entry):
        vals = self._prepare_reinvoice_line_vals(aml, dist_entry)
        return self.env['account.reinvoice.line'].create(vals)

    def _create_reinvoice_lines(self, amls):
        rlines = self.env['account.reinvoice.line']
        for aml in amls:
            dist = False
            key = aml.reinvoice_key_id
            for inst in key.key_instance_ids:
                if inst.state == 'confirm' \
                        and inst.date_start <= aml.date \
                        and inst.date_stop >= aml.date:
                    dist = inst.distribution_id
            if dist:
                for dist_entry in dist.distribution_line_ids:
                    rlines += self._create_reinvoice_line(aml, dist_entry)
            else:
                aml_ref = _("'%s' (ID:%s, Entry '%s')") % (
                    aml.name, aml.id, aml.move_id.name)
                self._note += _(
                    "\nJournal Item %s : "
                    "No valid Instance available for Reinvoice Key '%s'.") % (
                    aml_ref, key.name)
        return rlines

    def _reinvoice_aml_domain(self):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('reinvoice_line_ids', '=', False),
            ('move_id.state', '=', 'posted')]
        if self.date_from:
            domain += [('date', '>=', self.date_from)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        journal_in_ids = [x.id for x in self.journal_in_ids]
        if journal_in_ids:
            domain += [('journal_id', 'in', journal_in_ids)]
        reinvoice_key_ids = [x.id for x in self.reinvoice_key_ids]
        if reinvoice_key_ids:
            domain += [('reinvoice_key_id', 'in', reinvoice_key_ids)]
        else:
            domain += [('reinvoice_key_id', '!=', False)]
        return domain

    def _reinvoice_amls(self):
        domain = self._reinvoice_aml_domain()
        return self.env['account.move.line'].search(domain)

    def _generate(self):
        self._note = ''
        time_start = time.time()
        amls = self._reinvoice_amls()
        reinvoice_lines = self._create_reinvoice_lines(amls)
        # Commit after reinvoice line create to make processing time shorter
        # when the job gets killed for whatever reason
        # (large reinvoice jobs can take several hours).
        # The transactional integrity is not impacted.
        self._cr.commit()
        if self.uninvoiced:
            reinvoice_lines = self.env['account.reinvoice.line'].search(
                [('invoice_line_out_id', '=', False),
                 ('company_id', '=', self.company_id.id)])
        inv_ids, ref_ids = self._create_invoices(reinvoice_lines)
        note = _("Number of Selected Journal Items: %s") % len(amls) + "\n"
        note += _(
            "Number of Outgoing Invoices: %s") % len(inv_ids) + "\n"
        note += _(
            "Number of Outgoing Refunds: %s") % len(ref_ids) + "\n"
        time_end = time.time() - time_start
        note += _("Processing time = %.3f seconds") % time_end
        if self._note:
            note += "\n\n" + _("Remarks") + ":\n"
            note += self._note
        self.note = note
        return inv_ids, ref_ids

    @api.multi
    def generate(self):
        self.ensure_one()
        out_invoice_ids, out_refund_ids = self._generate()
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.account_reinvoice_wizard_view_form_result' % module)
        return {
            'name': _("Manual Reinvoice"),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.reinvoice.wizard',
            'view_id': result_view.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'out_invoice_ids': out_invoice_ids,
                'out_refund_ids': out_refund_ids}
        }

    @api.multi
    def action_view_invoice(self):
        act = self.env.ref('account.action_invoice_tree1')
        act_window = act.read()[0]
        act_window['domain'] = [
            ('id', 'in', self._context['out_invoice_ids'])]
        return act_window

    @api.multi
    def action_view_refund(self):
        act = self.env.ref('account.action_invoice_tree3')
        act_window = act.read()[0]
        act_window['domain'] = [
            ('id', 'in', self._context['out_refund_ids'])]
        return act_window
