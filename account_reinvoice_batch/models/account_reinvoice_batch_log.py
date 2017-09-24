# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class AccountReinvoiceBatchLog(models.Model):
    _name = 'account.reinvoice.batch.log'
    _description = 'Object to store the Reinvoice Service Logs'
    _order = 'date desc, name desc'

    name = fields.Char(
        required=True, readonly=True)
    date = fields.Datetime(
        string='Log Creation Date', readonly=True,
        default=fields.Datetime.now())
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('error', 'Error'),
                   ('done', 'Done')],
        required=True, readonly=True, default='draft')
    inv_count = fields.Integer(
        string='Number of Invoices', required=True,
        readonly=True, default=0,
        help="Number of Ougoing Invoices/Refunds Created")
    error_count = fields.Integer(
        string='Number of Errors', required=True,
        readonly=True, default=0)
    user_id = fields.Many2one(
        comodel_name='res.users', string='User', readonly=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', readonly=True,
        default=lambda self: self.env.user.company_id)
    note = fields.Text(
        string='Notes', readonly=True)

    @api.multi
    def unlink(self):
        for log in self:
            if log.state != 'draft':
                raise UserError(
                    _("Only log objects in state 'draft' can be deleted !"))
        return super(AccountReinvoiceBatchLog, self).unlink()

    @api.multi
    def button_done(self):
        self.state = 'done'
