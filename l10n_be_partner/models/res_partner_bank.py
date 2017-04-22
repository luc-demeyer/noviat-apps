# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def create(self, cr, uid, vals, context=None):
        if vals.get('state') != 'iban':
            env = api.Environment(cr, uid, context)
            bank = env['res.bank'].browse(vals.get('bank'))
            if bank.country == env.ref('base.be') and bank.bic and bank.code:
                vals['state'] = 'iban'
                vals['acc_number'] = \
                    env['res.bank'].bban2iban('be', vals['acc_number'])
        return super(ResPartnerBank, self).create(cr, uid, vals, context)
