# -*- coding: utf-8 -*-
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields


class res_bank(orm.Model):
    _inherit = 'res.bank'
    _columns = {
        'code': fields.char('Code', size=3,
            help='Country specific Bank Code (used for bban to iban conversion).'),
    }
