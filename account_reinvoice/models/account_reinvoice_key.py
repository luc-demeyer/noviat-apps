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
from openerp.exceptions import ValidationError


class AccountReinvoiceKey(models.Model):
    _name = 'account.reinvoice.key'
    _description = 'Reinvoice Key'
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'The Reinvocie Key must be unique per Company!'),
        ]

    name = fields.Char(
        string='Name', index=True, required=True)
    description = fields.Char(
        string='Description')
    key_instance_ids = fields.One2many(
        comodel_name='account.reinvoice.key.instance',
        inverse_name='reinvoice_key_id',
        string='Key Instances')
    active = fields.Boolean(
        string='Active', default=True,
        help="If the active field is set to False, "
             "it will allow you to hide the "
             "Reinvoice Key without removing it.")
    company_id = fields.Many2one(
        'res.company', string='Company')
    display_name = fields.Char(
        compute='_compute_display_name', string="Display Name",
        store=True, readonly=True)

    @api.one
    @api.depends('name', 'description')
    def _compute_display_name(self):
        display_name = self.name
        if self.description:
            display_name += ' ' + self.description
        self.display_name = len(display_name) > 55 \
            and display_name[:55] + '...' \
            or display_name


class AccountReinvoiceKeyInstance(models.Model):
    _name = 'account.reinvoice.key.instance'
    _description = 'Reinvoice Key Instance'
    _order = 'date_start desc'

    reinvoice_key_id = fields.Many2one(
        comodel_name='account.reinvoice.key', index=True,
        string='Reinvoice Key', ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ], string='Status',
        index=True, readonly=True, default='draft', copy=False)
    date_start = fields.Date(
        string='Start Date', required=True,
        states={'confirm': [('readonly', True)]})
    date_stop = fields.Date(
        string='End Date', required=True,
        states={'confirm': [('readonly', True)]})
    distribution_id = fields.Many2one(
        comodel_name='account.reinvoice.distribution',
        string='Distribution', index=True, required=True,
        states={'confirm': [('readonly', True)]})

    @api.one
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        if self.date_stop < self.date_start:
            raise ValidationError(
                _("The start date of an instance must precede its end date."))

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def confirm(self):
        self.ensure_one()
        confirmed_instances = [
            i for i in self.reinvoice_key_id.key_instance_ids
            if i.state == 'confirm']
        overlap = False
        for ci in confirmed_instances:
            if self[0].date_start < ci.date_start \
                    and self[0].date_stop > ci.date_stop:
                overlap = True
                break
            for dt in [self[0].date_start, self[0].date_stop]:
                if dt >= ci.date_start and dt <= ci.date_stop:
                    overlap = True
                    break
        if overlap:
            raise ValidationError(
                _("Overlapping period, correct the start/end dates."))
        self.write({'state': 'confirm'})
        return True
