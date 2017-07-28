# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_partner_flag = fields.Boolean(
        string="Partner Record associated to a Company Record")
    intercompany_invoice = fields.Boolean(
        string='Intercompany Invoice',
        help="Set this flag to convert outgoing invoices "
             "for this partner into incoming invoices in "
             "the Company associated with this partner.")
    intercompany_invoice_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Intercompany Invoice User',
        _prefetch=False,
        help="This user will be used "
             "to create/read/modify intercompany invoices in "
             "the Company associated with this partner.")

    @api.one
    @api.constrains('intercompany_invoice_user_id')
    def _check_intercompany_invoice_user_id(self):
        ic_user = self.intercompany_invoice_user_id
        if ic_user:
            cpy = self.env['res.company'].search(
                [('partner_id', '=', self.id)])
            if cpy and cpy not in ic_user.company_ids:
                raise ValidationError(
                    _("The Intercompany Invoice User doesn't have "
                      "privileges in Company '%s' !")
                    % cpy.name)

    def _auto_init(self, cr, context=None):
        """ set company_partner_flag """
        res = super(ResPartner, self)._auto_init(cr, context=context)
        cr.execute(
            "UPDATE res_partner p "
            "SET company_partner_flag = True "
            "FROM res_company c "
            "WHERE c.partner_id = p.id")
        return res
