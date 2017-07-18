# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
from sys import exc_info

from fintech.ebics import EbicsKeyRing, EbicsBank, EbicsUser, EbicsClient,\
    EbicsFunctionalError, EbicsTechnicalError, EbicsVerificationError

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)

"""
TODO:
add support for H003, cf. fintech doc:

To support EBICS protocol version H003 you must generate
the required order ids by yourself.
Therefore you have to subclass EbicsBank as follows:

class MyBank(EbicsBank):

    def _next_order_id(self, partnerid):
        # Generate an order id uniquely for each partner id
        # Must be a string between 'A000' and 'ZZZZ'
        return generate_order_id(partnerid)
"""


class EbicsXfer(models.TransientModel):
    _name = 'ebics.xfer'
    _description = 'EBICS file transfer'

    ebics_config_id = fields.Many2one(
        comodel_name='ebics.config',
        string='EBICS Configuration',
        required=True,
        default=lambda self: self._default_ebics_config_id())
    ebics_passphrase = fields.Char(
        string='EBICS Passphrase')
    date_from = fields.Date()
    date_to = fields.Date()
    format_id = fields.Many2one(
        comodel_name='ebics.file.format',
        string='EBICS File Format',
        help="Select EBICS File Format to download."
             "\nLeave blank to download all available files.")
    note = fields.Text(string='EBICS file transfer Log', readonly=True)

    @api.model
    def _default_ebics_config_id(self):
        cfg_mod = self.env['ebics.config']
        cfg = cfg_mod.search(
            [('company_id', '=', self.env.user.company_id.id)])
        if cfg and len(cfg) == 1:
            return cfg
        else:
            return cfg_mod

    @api.onchange('ebics_config_id')
    def _onchange_ebics_config_id(self):
        if self._context.get('ebics_download'):
            download_formats = self.ebics_config_id.ebics_file_format_ids\
                .filtered(lambda r: r.type == 'fdl')
            if len(download_formats) == 1:
                self.format_id = download_formats

    @api.multi
    def ebics_upload(self):
        self.ensure_one()
        self.note = ''
        client = self._setup_client()
        raise UserError(_(
            "The EBICS Upload functionality is not "
            "available in this version of the "
            "'account_ebics' module."))

    @api.multi
    def ebics_download(self):
        self.ensure_one()
        self.note = ''
        client = self._setup_client()
        download_formats = self.format_id \
            or self.ebics_config_id.ebics_file_format_ids.filtered(
                lambda r: r.type == 'fdl')
        ebics_files = self.env['ebics.file']
        for df in download_formats:
            try:
                data = client.FDL(
                    filetype=df.name, start=self.date_from or None,
                    end=self.date_to or None)
                ebics_files += self._handle_download_data(data, df)
                self.note += '\n'
                self.note += _(
                    "EBICS File '%s' is available for further processing."
                ) % ebics_files[-1].name
            except EbicsFunctionalError:
                e = exc_info()
                self.note += '\n'
                self.note += _("EBICS Functional Error:")
                self.note += '\n'
                self.note += '%s (code: %s)' % (e[1].message, e[1].code)
            except EbicsTechnicalError:
                e = exc_info()
                self.note += '\n'
                self.note += _("EBICS Technical Error:")
                self.note += '\n'
                self.note += '%s (code: %s)' % (e[1].message, e[1].code)
            except EbicsVerificationError:
                self.note += '\n'
                self.note += _("EBICS Verification Error:")
                self.note += '\n'
                self.note += _("The EBICS response could not be verified.")

        ctx = self._context.copy()
        ctx['ebics_file_ids'] = ebics_files._ids
        module = __name__.split('addons.')[1].split('.')[0]
        result_view = self.env.ref(
            '%s.ebics_xfer_view_form_result' % module)
        return {
            'name': _('EBICS file transfer result'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ebics.xfer',
            'view_id': result_view.id,
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def button_close(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def view_ebics_file(self):
        self.ensure_one()
        module = __name__.split('addons.')[1].split('.')[0]
        act = self.env['ir.actions.act_window'].for_xml_id(
            module, 'ebics_file_action')
        act['domain'] = [('id', 'in', self._context['ebics_file_ids'])]
        return act

    @api.multi
    def _setup_client(self):
        passphrase = self._get_passphrase()
        keyring = EbicsKeyRing(
            keys=self.ebics_config_id.ebics_keys,
            passphrase=passphrase)
        bank = EbicsBank(
            keyring=keyring,
            hostid=self.ebics_config_id.ebics_host,
            url=self.ebics_config_id.ebics_url)
        user = EbicsUser(
            keyring=keyring,
            partnerid=self.ebics_config_id.ebics_partner,
            userid=self.ebics_config_id.ebics_user)
        client = EbicsClient(
            bank, user, version=self.ebics_config_id.ebics_version)
        return client

    def _get_passphrase(self):
        passphrase = self.ebics_config_id.ebics_passphrase

        if passphrase:
            return passphrase

        module = __name__.split('addons.')[1].split('.')[0]
        passphrase_view = self.env.ref(
            '%s.ebics_xfer_view_form_passphrase' % module)
        return {
            'name': _('EBICS file transfer'),
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ebics.xfer',
            'view_id': passphrase_view.id,
            'target': 'new',
            'context': self._context,
            'type': 'ir.actions.act_window',
        }

    def _file_format_methods(self):
        """
        Extend this dictionary in order to add support
        for extra file formats.
        """
        res = {
            'camt.xxx.cfonb120.stm': self._handle_cfonb120,
        }
        return res

    def _handle_download_data(self, data, file_format):
        """
        Write the data as received over the EBICS connection
        to a temporary file so that is is available for
        analysis (e.g. in case formats are received that cannot
        be handled in the current version of this module).

        TODO: add code to clean-up /tmp on a regular basis.

        After saving the data received we call the method to perform
        file format specific processing.
        """
        ebics_files_root = self.ebics_config_id.ebics_files
        tmp_dir = os.path.normpath(ebics_files_root + '/tmp')
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir, 0700)
        fn_date = self.date_to or fields.Date.today()
        base_fn = '_'.join(
            [self.ebics_config_id.ebics_host, fn_date])
        n = 1
        fn = base_fn + '_' + str(n).rjust(3, '0')
        full_tmp_fn = os.path.normpath(tmp_dir + '/' + fn)
        while os.path.exists(full_tmp_fn):
            n += 1
            tmp_fn = base_fn + str(n).rjust(3, '0')
            full_tmp_fn = os.path.normpath(tmp_dir + '/' + tmp_fn)

        with open(full_tmp_fn, 'wb') as f:
            f.write(data)

        ff_methods = self._file_format_methods()
        if file_format.name in ff_methods:
            data = ff_methods[file_format.name](data)

        fn = '.'.join([base_fn, file_format.suffix])
        self._check_duplicate_ebics_file(fn)
        data = base64.encodestring(data)
        ebics_file = self.env['ebics.file'].create({
            'name': fn,
            'data': data,
            'download_date': fields.Datetime.now(),
            'date_from': self.date_from,
            'date_to': self.date_from,
            'format_id': file_format.id,
            'user_id': self._uid,
        })

        return ebics_file

    def _check_duplicate_ebics_file(self, fn):
        dups = self.env['ebics.file'].search(
            [('name', '=', fn),
             '|',
             ('company_id', '=', self.env.user.company_id.id),
             ('company_id', '=', False)])
        if dups:
            raise UserError(_(
                "EBICS File with name '%s' has already been downloaded."
                "\nPlease check this file and rename in case there is "
                "no risk on duplicate transactions.")
                % fn)

    def _insert_line_terminator(self, data_in, line_len):
        data_out = ''
        max = len(data_in)
        i = 0
        while i + line_len <= max:
            data_out += data_in[i:i + line_len] + '\n'
            i += line_len
        return data_out

    def _handle_cfonb120(self, data_in):
        return self._insert_line_terminator(data_in, 120)

    def _handle_cfonb240(self, data_in):
        return self._insert_line_terminator(data_in, 240)
