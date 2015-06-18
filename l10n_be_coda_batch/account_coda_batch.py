# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011-2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class account_coda_batch_log(models.Model):
    _name = 'account.coda.batch.log'
    _description = 'Object to store CODA Batch Import Logs'
    _order = 'name desc'

    name = fields.Char(string='Name', required=True)
    directory = fields.Char(
        string='CODA Batch Import Folder',
        required=True, readonly=True,
        help='Folder containing the CODA Files for the batch import.')
    log_ids = fields.One2many(
        'coda.batch.log.item', 'batch_id',
        string='Batch Import Log Items', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('done', 'Done')],
        string='State', required=True, readonly=True, default='draft')
    date = fields.Date(
        string='Log Creation Date', readonly=True,
        default=fields.Date.today())
    user_id = fields.Many2one(
        'res.users', string='User', readonly=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('dir_uniq', 'unique (directory_id)',
         'This folder has already been processed !')
    ]

    @api.one
    def button_cancel(self):
        self.state = 'draft'

    @api.one
    def button_done(self):
        self.state = 'done'

    @api.one
    def button_import(self):
        ctx = self._context.copy()
        ctx.update({
            'active_model': 'account.coda.batch.log',
            'active_id': self.id,
            'coda_batch_restart': True,
        })
        self.env['account.coda.batch.import'].with_context(
            ctx).coda_batch_import()

    @api.multi
    def unlink(self):
        for log in self:
            if log.state != 'draft':
                raise Warning(
                    _("Only log objects in state 'draft' can be deleted !"))
        return super(account_coda_batch_log, self).unlink()


class coda_batch_log_item(models.Model):
    _name = 'coda.batch.log.item'
    _description = 'Object to store CODA Batch Import Log Items'
    _order = 'date desc'
    _rec_name = 'batch_id'

    batch_id = fields.Many2one(
        'account.coda.batch.log', string='Import Object',
        ondelete='cascade', readonly=True)
    date = fields.Datetime(
        string='Log Creation Time', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('done', 'Done')],
        string='State', required=True, readonly=True)
    note = fields.Text(
        string='Batch Import Log', readonly=True)
    file_count = fields.Integer(
        string='Number of Files', required=True, default=0)
    error_count = fields.Integer(
        string='Number of Errors', required=True, default=0)
    user_id = fields.Many2one(
        'res.users', string='User', readonly=True,
        default=lambda self: self.env.user)
