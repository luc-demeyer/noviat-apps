# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountCodaBatchLog(models.Model):
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
    reconcile = fields.Boolean(
        help="Launch Automatic Reconcile after CODA import.", default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('dir_uniq', 'unique (directory)',
         'This folder has already been processed !')
    ]

    @api.multi
    def unlink(self):
        for log in self:
            if log.state != 'draft':
                raise UserError(
                    _("Only log objects in state 'draft' can be deleted !"))
        return super(AccountCodaBatchLog, self).unlink()

    @api.multi
    def button_cancel(self):
        self.state = 'draft'

    @api.multi
    def button_done(self):
        self.state = 'done'

    @api.multi
    def button_import(self):
        self.ensure_one()
        ctx = self._context.copy()
        ctx.update({
            'active_model': 'account.coda.batch.log',
            'active_id': self.id,
            'coda_batch_restart': True,
            'automatic_reconcile': self.reconcile,
        })
        self.env['account.coda.batch.import'].with_context(
            ctx).coda_batch_import()


class CodaBatchLogItem(models.Model):
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
