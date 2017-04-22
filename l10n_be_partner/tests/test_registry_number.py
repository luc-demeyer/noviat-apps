# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class TestRegistryNumber(TransactionCase):

    def setUp(self):
        super(TestRegistryNumber, self).setUp()
        cr, uid = self.cr, self.uid
        self.rp_model = self.registry('res.partner')
        self.rp_id = self.registry('ir.model.data').get_object_reference(
            cr, uid, 'l10n_be_partner', 'res_partner_1')[1]

    def test_registry_number(self):
        cr, uid = self.cr, self.uid
        self.rp_model.write(cr, uid, [self.rp_id], {'vat': 'BE 0820 512 013'})
        rp = self.rp_model.browse(cr, uid, self.rp_id)
        self.assertEqual(rp.registry_authority, 'kbo_bce')
        self.assertEqual(rp.registry_number, '0820.512.013')
