# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
import time
from sys import exc_info
from traceback import format_exception

from odoo import api, fields, models, _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountCodaBatchImport(models.TransientModel):
    _name = 'account.coda.batch.import'
    _description = 'CODA Batch Import'

    directory = fields.Selection(
        '_get_directory',
        'CODA Batch Import Folder', required=True,
        default=lambda self: self._default_directory(),
        help='Folder containing the CODA Files for the batch import.')
    note = fields.Text(string='Batch Import Log', readonly=True)
    reconcile = fields.Boolean(
        help="Launch Automatic Reconcile after CODA import.", default=True)

    @api.model
    def _default_directory(self):
        res = self._get_directory()
        return res[0]

    @api.model
    def _get_directory(self):
        company = self.env.user.company_id
        coda_batch_root = company.coda_batch_root
        path = os.path.normpath(coda_batch_root)
        folder_start = len(path)

        self._cr.execute(
            "SELECT directory FROM account_coda_batch_log "
            "WHERE company_id = %s", (company.id,))
        processed = [x[0] for x in self._cr.fetchall()]

        selection = []
        for root, folders, files in os.walk(path, followlinks=False):
            if files:
                folder = root[folder_start + 1:]
                if folder not in processed:
                    selection.append((folder, folder))
        return selection or [('none', _('None'))]

    @api.onchange('directory')
    def _onchange_directory(self):
        if self.directory == 'none':
            self.note = _("No unprocessed Batch Import Folders found !")

    @api.model
    def view_init(self, fields_list):
        company = self.env.user.company_id
        coda_batch_root = company.coda_batch_root
        if not coda_batch_root:
            raise UserError(
                _("Configuration Error!"
                  "\nNo Root Directory configured for CODA Batch Folders !"))
        path = os.path.normpath(coda_batch_root)
        if not os.path.exists(path):
            raise UserError(
                _("Configuration Error!"
                  "\nPath %s does not exist.")
                % path)

    @api.multi
    def coda_batch_import(self):
        ctx = self._context.copy()
        restart = ctx.get('coda_batch_restart')
        batch_obj = self.env['account.coda.batch.log']
        log_obj = self.env['coda.batch.log.item']
        coda_import_wiz = self.env['account.coda.import']

        note = False
        if restart:
            if ctx.get('active_model') == 'account.coda.batch.log':
                coda_batch = batch_obj.browse(ctx.get('active_id'))
                directory = coda_batch.directory
            else:
                raise UserError(
                    _("Programming Error"))
        else:
            directory = self.directory

        company = self.env.user.company_id
        coda_batch_root = company.coda_batch_root
        path = os.path.normpath(coda_batch_root + '/' + directory)
        files = os.listdir(path)
        log_date = time.strftime('%Y-%m-%d %H:%M:%S')
        log_header = _('>>> Import by %s. Results:') % self.env.user.name
        log_footer = _('\n\nNumber of files : %s\n\n') % str(len(files))
        self._log_note = ''
        self._nb_err = 0
        self._err_log = ''

        if not restart:
            coda_batch = batch_obj.create(
                {'name': directory.split('/')[-1],
                 'directory': directory})
        self._cr.commit()
        ctx.update({'batch_id': coda_batch.id})
        coda_files = self._sort_files(path, files)

        # process CODA files
        for coda_file in coda_files:
            time_start = time.time()
            try:
                statements = coda_import_wiz._coda_parsing(
                    codafile=coda_file[1], codafilename=coda_file[2],
                    batch=True)
                if self.reconcile or self._context.get('automatic_reconcile'):
                    reconcile_note = ''
                    for statement in statements:
                        reconcile_note = coda_import_wiz._automatic_reconcile(
                            statement, reconcile_note=reconcile_note)
                    if reconcile_note:
                        self._log_note += reconcile_note
                self._log_note += _(
                    "\n\nCODA File '%s' has been imported.\n"
                    ) % coda_file[2]
            except UserError, e:
                self._nb_err += 1
                self._err_log += _(
                    "\n\nError while processing CODA File '%s' :\n%s"
                    ) % (coda_file[2], ''.join(e.args))
            except:
                self._nb_err += 1
                tb = ''.join(format_exception(*exc_info()))
                self._err_log += _(
                    "\n\nError while processing CODA File '%s' :\n%s"
                    ) % (coda_file[2], tb)
            file_import_time = time.time() - time_start
            _logger.warn(
                'File %s processing time = %.3f seconds',
                coda_file[2], file_import_time)

        if self._nb_err:
            log_state = 'error'
        else:
            log_state = 'done'

        if self._err_log or self._log_note:
            note = self._err_log + self._log_note

        log_obj.create({
            'batch_id': coda_batch.id,
            'date': log_date,
            'state': log_state,
            'note': note,
            'file_count': len(files),
            'error_count': self._nb_err,
            })
        coda_batch.state = log_state

        if restart:
            return True
        else:
            module = __name__.split('addons.')[1].split('.')[0]
            result_view = self.env.ref(
                '%s.account_coda_batch_import_view_form_result' % module)

            note = note or ""
            self.note = log_header + '\n' + note + log_footer
            return {
                'name': _('CODA Batch Import result'),
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.coda.batch.import',
                'view_id': result_view.id,
                'target': 'new',
                'context': ctx,
                'type': 'ir.actions.act_window',
            }

    @api.multi
    def action_open_log(self):
        self.ensure_one
        return {
            'name': _('CODA Batch Import Log'),
            'res_id': self._context.get('batch_id'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.coda.batch.log',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    def _msg_duplicate(self, filename):
        self._nb_err += 1
        self._err_log += _(
            "\n\nError while processing CODA File '%s' :"
            ) % (filename)
        self._err_log += _(
            "\nThis CODA File is marked by your bank as a 'Duplicate' !"
            )
        self._err_log += _(
            '\nPlease treat this CODA File manually !')

    def _msg_exception(self, filename):
        self._nb_err += 1
        self._err_log += _(
            "\n\nError while processing CODA File '%s' :") % (filename)
        self._err_log += _('\nInvalid Header Record !')

    def _msg_noheader(self, filename):
        self._nb_err += 1
        self._err_log += _(
            "\n\nError while processing CODA File '%s' :") % (filename)
        self._err_log += _("\nMissing Header Record !")

    def _sort_files(self, path, files):
        """
        Sort CODA files on creation date
        """
        coda_files = []
        for filename in files:
            coda_creation_date = False
            with open(path + '/' + filename, 'r') as codafile:
                data = codafile.read()
                recordlist = unicode(
                    data, 'windows-1252', 'strict').split('\n')
                if not recordlist:
                    self._nb_err += 1
                    self._err_log += _(
                        "\n\nError while processing CODA File '%s' :"
                        ) % (filename)
                    self._err_log += _("\nEmpty File !")
                else:
                    for line in recordlist:
                        if not line:
                            pass
                        elif line[0] == '0':
                            try:
                                coda_creation_date = str2date(line[5:11])
                                if line[16] == 'D':
                                    self._msg_duplicate(filename)
                                else:
                                    coda_files += [
                                        (coda_creation_date,
                                         data,
                                         filename)]
                            except:
                                self._msg_exception(filename)
                            break
                        else:
                            self._msg_noheader(filename)
                            break
        coda_files.sort()
        return coda_files


def str2date(date_str):
    return time.strftime('%Y-%m-%d', time.strptime(date_str, '%d%m%y'))
