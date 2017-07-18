# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


"""
import logging
logging.basicConfig(
     level = logging.DEBUG,
     format = " %(levelname)s %(name)s: %(message)s",
)
"""

import base64
import os
from sys import exc_info

import fintech
fintech.register()
fintech.cryptolib = 'cryptography'
from fintech.ebics import EbicsKeyRing, EbicsBank, EbicsUser, EbicsClient,\
    EbicsFunctionalError, EbicsTechnicalError, EbicsVerificationError

from urllib2 import URLError

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError


class EbicsBank(EbicsBank):
    """
    EBICS protocol version H003 requires generation of the order ids.
    """

    def _next_order_id(self, partnerid):
        # Generate an order id uniquely for each partner id
        # Must be a string between 'A000' and 'ZZZZ'
        # TODO: implement generate_order_id
        # return generate_order_id(partnerid)
        return "A000"


class EbicsConfig(models.Model):
    """
    EBICS configuration is stored in a separate object in order to
    allow extra security policies on this object.

    Remark:
    This Configuration model implements a simple model of the relationship
    between users and authorizations and may need to be adapted
    in next versions of this module to cope with higher complexity .
    """
    _name = 'ebics.config'
    _description = 'EBICS Configuration'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        readonly=True, states={'draft': [('readonly', False)]},
        string='Bank Account', required=True)
    ebics_host = fields.Char(
        string='EBICS HostID', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Contact your bank to get the EBICS HostID."
             "\nIn France the BIC is usually allocated to the HostID "
             "whereas in Germany it tends to be an institute specific string "
             "of 8 characters.")
    ebics_url = fields.Char(
        string='EBICS URL', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Contact your bank to get the EBICS URL.")
    ebics_version = fields.Selection(
        selection=[('H003', 'H003 (2.4)'),
                   ('H004', 'H004 (2.5)')],
        string='EBICS protocol version',
        readonly=True, states={'draft': [('readonly', False)]},
        required=True, default='H004')
    ebics_partner = fields.Char(
        string='EBICS PartnerID', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Organizational unit (company or individual) "
             "that concludes a contract with the bank. "
             "\nIn this contract it will be agreed which order types "
             "(file formats) are used, which accounts are concerned, "
             "which of the customer’s users (subscribers) "
             "communicate with the EBICS bank server and the authorisations "
             "that these users will possess. "
             "\nIt is identified by the PartnerID.")
    ebics_user = fields.Char(
        string='EBICS UserID', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Human users or a technical system that is/are "
             "assigned to a customer. "
             "\nOn the EBICS bank server it is identified "
             "by the combination of UserID and PartnerID. "
             "The technical subscriber serves only for the data exchange "
             "between customer and financial institution. "
             "The human user also can authorise orders.")
    ebics_files = fields.Char(
        string='EBICS Files Root', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self._default_ebics_files(),
        help="Root Directory for EBICS File Transfer Folders.")

    # We store the EBICS keys in a separate directory in the file system.
    # This directory requires special protection to reduce fraude.
    ebics_keys = fields.Char(
        string='EBICS Keys', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self._default_ebics_keys(),
        help="File holding the EBICS Keys."
             "\nSpecify the full path (directory + filename).")
    ebics_passphrase = fields.Char(
        string='EBICS Passphrase',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_version = fields.Selection(
        selection=[('A005', 'A005 (RSASSA-PKCS1-v1_5)'),
                   ('A006', 'A006 (RSASSA-PSS)')],
        string='EBICS key version',
        default='A006',
        readonly=True, states={'draft': [('readonly', False)]},
        help="The key version of the electronic signature.")
    ebics_key_bitlength = fields.Integer(
        string='EBICS key bitlength',
        default=2048,
        readonly=True, states={'draft': [('readonly', False)]},
        help="The bit length of the generated keys. "
             "\nThe value must be between 1536 and 4096.")
    ebics_ini_letter = fields.Binary(
        string='EBICS INI Letter', readonly=True,
        help="INI-letter PDF document to be sent to your bank.")
    ebics_ini_letter_fn = fields.Char(
        string='INI-letter Filename', readonly=True)
    ebics_public_bank_keys = fields.Binary(
        string='EBICS Public Bank Keys', readonly=True,
        help="EBICS Public Bank Keys to be checked for consistency.")
    ebics_public_bank_keys_fn = fields.Char(
        string='EBICS Public Bank Keys Filename', readonly=True)

    # X.509 Distinguished Name attributes used to
    # create self-signed X.509 certificates
    ebics_key_x509_dn_cn = fields.Char(
        string='Common Name [CN]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_o = fields.Char(
        string='Organization Name [O]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_ou = fields.Char(
        string='Organizational Unit Name [OU]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_c = fields.Char(
        string='Country Name [C]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_st = fields.Char(
        string='State Or Province Name [ST]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_l = fields.Char(
        string='Locality Name [L]',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    ebics_key_x509_dn_e = fields.Char(
        string='Email Address',
        readonly=True, states={'draft': [('readonly', False)]},
    )

    ebics_file_format_ids = fields.Many2many(
        comodel_name='ebics.file.format',
        column1='config_id', column2='format_id',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('init', 'Initialisation'),
         ('get_bank_keys', 'Get Keys from Bank'),
         ('to_verify', 'Verification'),
         ('active', 'Active')],
        string='State',
        default='draft',
        required=True, readonly=True)
    active = fields.Boolean(
        string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id,
        required=True)

    @api.model
    def _default_ebics_files(self):
        return '/'.join(['/home/odoo/ebics_files', self._cr.dbname])

    @api.model
    def _default_ebics_keys(self):
        return '/'.join(['/etc/odoo/ebics_keys',
                         self._cr.dbname,
                         'mykeys'])

    @api.multi
    def unlink(self):
        for ebics_config in self:
            if ebics_config.state == 'active':
                raise UserError(_(
                    "You cannot remove active EBICS congirations."))
        return super(EbicsConfig, self).unlink()

    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def set_to_active(self):
        return self.write({'state': 'active'})

    @api.multi
    def ebics_init_1(self):
        """
        Initialization of bank keys - Step 1:
        Create new keys and certificates for this user
        """
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(
                _("Set state to 'draft' before Bank Key (re)initialisation."))

        keyring = EbicsKeyRing(
            keys=self.ebics_keys, passphrase=self.ebics_passphrase)
        bank = EbicsBank(
            keyring=keyring, hostid=self.ebics_host, url=self.ebics_url)
        user = EbicsUser(
            keyring=keyring, partnerid=self.ebics_partner,
            userid=self.ebics_user)

        dirname = os.path.dirname(self.ebics_keys)
        if not os.path.exists(dirname):
            raise UserError(_(
                "EBICS Keys Directory '%s' is not available."
                "Please contact your system administrator.")
                % dirname)

        user.create_keys(
            keyversion=self.ebics_key_version,
            bitlength=self.ebics_key_bitlength)

        dn_attrs = {
            'commonName': self.ebics_key_x509_dn_cn,
            'organizationName': self.ebics_key_x509_dn_o,
            'organizationalUnitName': self.ebics_key_x509_dn_ou,
            'countryName': self.ebics_key_x509_dn_c,
            'stateOrProvinceName': self.ebics_key_x509_dn_st,
            'localityName': self.ebics_key_x509_dn_l,
            'emailAddress': self.ebics_key_x509_dn_e,
        }
        kwargs = {k: v for k, v in dn_attrs.items() if v}
        user.create_certificates(**kwargs)

        client = EbicsClient(bank, user, version=self.ebics_version)

        # Send the public electronic signature key to the bank.
        try:
            OrderID = client.INI()
        except URLError:
            e = exc_info()
            raise UserError(_(
                "urlopen error:\n url '%s' - %s")
                % (self.ebics_url, e[1].reason.strerror))

        # Send the public authentication and encryption keys to the bank.
        OrderID = client.HIA()

        # Create an INI-letter which must be printed and sent to the bank.
        lang = self.env.user.lang[:2]
        cc = self.bank_id.country_id.code
        if cc in ['FR', 'DE']:
            lang = cc
        tmp_dir = os.path.normpath(self.ebics_files + '/tmp')
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir, 0700)
        fn_date = fields.Date.today()
        fn = '_'.join([self.ebics_host, 'ini_letter', fn_date]) + '.pdf'
        full_tmp_fn = os.path.normpath(tmp_dir + '/' + fn)
        user.create_ini_letter(
            bankname=self.bank_id.bank.name,
            path=full_tmp_fn,
            lang=lang)
        with open(full_tmp_fn, 'rb') as f:
            letter = f.read()
            self.write({
                'ebics_ini_letter': base64.encodestring(letter),
                'ebics_ini_letter_fn': fn,
            })

        return self.write({'state': 'init'})

    @api.multi
    def ebics_init_2(self):
        """
        Initialization of bank keys - Step 2:
        Activation of the account by the bank.
        """
        if self.state != 'init':
            raise UserError(
                _("Set state to 'Initialisation'."))
        self.ensure_one()
        return self.write({'state': 'get_bank_keys'})

    @api.multi
    def ebics_init_3(self):
        """
        Initialization of bank keys - Step 3:

        After the account has been activated the public bank keys
        must be downloaded and checked for consistency.
        """
        self.ensure_one()
        if self.state != 'get_bank_keys':
            raise UserError(
                _("Set state to 'Get Keys from Bank'."))
        keyring = EbicsKeyRing(
            keys=self.ebics_keys, passphrase=self.ebics_passphrase)
        bank = EbicsBank(
            keyring=keyring, hostid=self.ebics_host, url=self.ebics_url)
        user = EbicsUser(
            keyring=keyring, partnerid=self.ebics_partner,
            userid=self.ebics_user)
        client = EbicsClient(
            bank, user, version=self.ebics_config_id.ebics_version)

        public_bank_keys = client.HPB()
        tmp_dir = os.path.normpath(self.ebics_files + '/tmp')
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir, 0700)
        fn_date = fields.Date.today()
        fn = '_'.join([self.ebics_host, 'public_bank_keys', fn_date]) + '.txt'
        self.write({
            'ebics_ini_letter': base64.encodestring(public_bank_keys),
            'ebics_ini_letter_fn': fn,
            'state': 'to_verify',
        })

        return True

    @api.multi
    def ebics_init_4(self):
        """
        Initialization of bank keys - Step 2:
        Confirm Verification of the public bank keys
        and activate the bank keyu.
        """
        self.ensure_one()
        if self.state != 'to_verify':
            raise UserError(
                _("Set state to 'Verification'."))

        keyring = EbicsKeyRing(
            keys=self.ebics_keys, passphrase=self.ebics_passphrase)
        bank = EbicsBank(
            keyring=keyring, hostid=self.ebics_host, url=self.ebics_url)
        bank.activate_keys()
        return self.write({'state': 'active'})
