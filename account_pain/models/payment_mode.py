# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.osv import fields, orm

import logging
_logger = logging.getLogger(__name__)


class payment_mode(orm.Model):
    _inherit = 'payment.mode'

    def _initiatingparty_default(self, cr, uid, field, context=None):
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        vat = company.partner_id.vat
        # Belgium, febelfin specs
        if vat and vat[0:2].upper() == 'BE':
            kbo_nr = vat[2:].replace(' ', '')
            if field == 'id':
                return kbo_nr
            else:
                return 'KBO-BCE'
        else:
            # complete for other countries
            return False

    def _initiatingparty_id_default(self, cr, uid, context=None):
        return self._initiatingparty_default(cr, uid, 'id', context=context)

    def _initiatingparty_issr_default(self, cr, uid, context=None):
        return self._initiatingparty_default(cr, uid, 'issr', context=context)

    _columns = {
        'type': fields.selection(
            [('manual', 'Manual'),
             ('iso20022', 'ISO 20022')],
            'Type', select=1,
            help='Select the Payment Type for the Payment Mode.'),
        'bank_id': fields.many2one(
            'res.partner.bank', "Bank account",
            required=False, help='Bank Account for the Payment Mode'),
        'initgpty_id': fields.char(
            'Initiating Party Id', size=35,
            help="Identifier of the Initiating Party."
                 "\nSpecify KBO-BCE number for Belgium."
                 "\n(Field: InitgPty.Id.OrgId.Othr.Id)"),
        'initgpty_issr': fields.char(
            'Initiating Party Id Issuer', size=35,
            help="Issuer of the Identifier of the Initiating Party."
                 "\nSpecify 'KBO-BCE' for Belgium."
                 "\n(Field: InitgPty.Id.OrgId.Othr.Issr)"),
    }
    _defaults = {
        'initgpty_id': _initiatingparty_id_default,
        'initgpty_issr': _initiatingparty_issr_default,
    }

    def _check_initiatingparty_id(self, cr, uid, ids, context=None):
        pm = self.browse(cr, uid, ids[0], context=context)
        if pm.initgpty_issr and not pm.initgpty_id:
            return False
        return True

    _constraints = [
        (_check_initiatingparty_id,
         "Configuration Error! Please complete "
         "the 'Initiating Party Id' field.",
         ['initgpty_id'])
    ]
