# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestKboBceNumber(TransactionCase):

    def setUp(self):
        super(TestKboBceNumber, self).setUp()
        self.rp_1 = self.env.ref('l10n_be_partner_kbo_bce.res_partner_1')
        self.be = self.env.ref('base.be')

    def test_validate_kbo_bce_number(self):
        rp = self.rp_1
        with self.assertRaises(ValidationError):
            rp.kbo_bce_number = '0820 512 014'

    def test_assign_kbo_bce_number(self):
        rp = self.rp_1
        rp.vat = 'BE 0820 512 013'
        self.assertEqual(rp.country_id, self.be)
        self.assertEqual(rp.kbo_bce_number, '0820.512.013')

    def test_check_vat_consistency(self):
        rp = self.rp_1
        rp.vat = 'BE 0820 512 013'
        with self.assertRaises(ValidationError):
            rp.kbo_bce_number = '0477.472.701'

    def test_format_kbo_bce_number(self):
        rp = self.rp_1
        rp.vat = 'BE 0820 512 013'
        rp.kbo_bce_number = '0820512013'
        rp.invalidate_cache(['kbo_bce_number'])
        self.assertEqual(rp.kbo_bce_number, '0820.512.013')

    def test_create_be_partner(self):
        rp_vals = {
            'name': 'BeCo',
            'vat': 'BE 0820 512 013',
            'is_company': True,
        }
        rp = self.env['res.partner'].create(rp_vals)
        self.assertEqual(rp.country_id, self.be)
        self.assertEqual(rp.kbo_bce_number, '0820.512.013')
