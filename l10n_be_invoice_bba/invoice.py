# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
import time
import random
from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

"""
account.invoice object:
    - Add support for Belgian structured communication
    - Rename 'reference' field labels to 'Communication'
"""


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def _get_reference_type(self, cr, uid, context=None):
        """
        Add BBA Structured Communication Type and change labels from 'reference' into 'communication'
        """
        res = super(account_invoice, self)._get_reference_type(cr, uid, context=context)
        res[[i for i, x in enumerate(res) if x[0] == 'none'][0]] = ('none', 'Free Communication')
        res.append(('bba', 'BBA Structured Communication'))
        return res

    def check_bbacomm(self, val):
        supported_chars = '0-9+*/ '
        pattern = re.compile('[^' + supported_chars + ']')
        if pattern.findall(val or ''):
            return False
        bbacomm = re.sub('\D', '', val or '')
        if len(bbacomm) == 12:
            base = int(bbacomm[:10])
            mod = base % 97 or 97
            if mod == int(bbacomm[-2:]):
                return True
        return False

    def duplicate_bba(self, cr, uid, inv_type, reference, partner):
        """ overwrite this method to customise the handling of duplicate BBA communications """
        error = False
        reference_type = 'bba'
        partner = partner.commercial_partner_id  # replace by the partner for which the accounting entries will be created
        if inv_type == 'out_invoice':
                if partner.out_inv_comm_algorithm == 'random':
                    # generate new bbacom to cope with following situation duplicate bba coming out of random generator
                    reference = self.generate_bbacomm(cr, uid, [], inv_type, reference_type, partner.id, False)['value']['reference']
                else:
                    # replace duplicate BBA Comms created manually or by OpenERP applications (e.g. Sales Order Refund/Modify)
                    reference = self.generate_bbacomm(cr, uid, [], inv_type, reference_type, partner.id, False)['value']['reference']
        if error:
            raise orm.except_orm(_('Warning!'),
                _('The BBA Structured Communication has already been used!' \
                  '\nPlease use a unique BBA Structured Communication.'))
        return reference_type, reference

    def _check_communication(self, cr, uid, ids):
        for inv in self.browse(cr, uid, ids):
            if inv.reference_type == 'bba':
                return self.check_bbacomm(inv.reference)
        return True

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
            date_invoice, payment_term, partner_bank_id, company_id)
        reference = False
        reference_type = 'none'
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner = partner.commercial_partner_id  # replace by the partner for which the accounting entries will be created
            if type in ['out_invoice']:
                reference_type = partner.out_inv_comm_type or 'none'
                if (type == 'out_invoice'):
                    if reference_type == 'bba':
                        reference = self.generate_bbacomm(cr, uid, ids, type, reference_type, partner.id, reference)['value']['reference']
        res_update = {
            'reference_type': reference_type or 'none',
            'reference': reference,
        }
        result['value'].update(res_update)
        return result

    def generate_bbacomm(self, cr, uid, ids, type, reference_type, partner_id, reference, context=None):
        reference = reference or ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner = partner.commercial_partner_id  # replace by the partner for which the accounting entries will be created
            if not reference_type:
                reference_type = partner.out_inv_comm_type
            if (type == 'out_invoice'):
                if reference_type == 'bba':
                    algorithm = partner.out_inv_comm_algorithm or 'random'
                    if algorithm == 'date':
                        if not self.check_bbacomm(reference):
                            doy = time.strftime('%j')
                            year = time.strftime('%Y')
                            seq = '001'
                            seq_ids = self.search(cr, uid,
                                [('type', '=', 'out_invoice'), ('reference_type', '=', 'bba'),
                                 ('reference', 'like', '+++%s/%s/%%' % (doy, year))], order='reference')
                            if seq_ids:
                                prev_seq = int(self.browse(cr, uid, seq_ids[-1]).reference[12:15])
                                if prev_seq < 999:
                                    seq = '%03d' % (prev_seq + 1)
                                else:
                                    raise orm.except_orm(_('Warning!'),
                                        _('The daily maximum of outgoing invoices with an automatically generated BBA Structured Communications has been exceeded!' \
                                          '\nPlease create manually a unique BBA Structured Communication.'))
                            bbacomm = doy + year + seq
                            base = int(bbacomm)
                            mod = base % 97 or 97
                            reference = '+++%s/%s/%s%02d+++' % (doy, year, seq, mod)
                    elif algorithm == 'partner_ref':
                        if not self.check_bbacomm(reference):
                            partner_ref = partner.ref
                            partner_ref_nr = re.sub('\D', '', partner_ref or '')
                            if (len(partner_ref_nr) < 3) or (len(partner_ref_nr) > 7):
                                raise orm.except_orm(_('Warning!'),
                                    _('The Partner should have a 3-7 digit Reference Number for the generation of BBA Structured Communications!' \
                                      '\nPlease correct the Partner record.'))
                            else:
                                partner_ref_nr = partner_ref_nr.ljust(7, '0')
                                seq = '001'
                                seq_ids = self.search(cr, uid,
                                    [('type', '=', 'out_invoice'), ('reference_type', '=', 'bba'),
                                     ('reference', 'like', '+++%s/%s/%%' % (partner_ref_nr[:3], partner_ref_nr[3:]))], order='reference')
                                if seq_ids:
                                    prev_seq = int(self.browse(cr, uid, seq_ids[-1]).reference[12:15])
                                    if prev_seq < 999:
                                        seq = '%03d' % (prev_seq + 1)
                                    else:
                                        raise orm.except_orm(_('Warning!'),
                                            _('The daily maximum of outgoing invoices with an automatically generated BBA Structured Communications has been exceeded!' \
                                              '\nPlease create manually a unique BBA Structured Communication.'))
                            bbacomm = partner_ref_nr + seq
                            base = int(bbacomm)
                            mod = base % 97 or 97
                            reference = '+++%s/%s/%s%02d+++' % (partner_ref_nr[:3], partner_ref_nr[3:], seq, mod)
                    elif algorithm == 'random':
                        if not self.check_bbacomm(reference):
                            base = random.randint(1, 9999999999)
                            bbacomm = str(base).rjust(10, '0')
                            base = int(bbacomm)
                            mod = base % 97 or 97
                            mod = str(mod).rjust(2, '0')
                            reference = '+++%s/%s/%s%s+++' % (bbacomm[:3], bbacomm[3:7], bbacomm[7:], mod)
                    else:
                        raise orm.except_orm(_('Error!'),
                            _("Unsupported Structured Communication Type Algorithm '%s' !" \
                              "\nPlease contact your OpenERP support channel.") % algorithm)
        return {'value': {'reference': reference}}

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        res = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date, period_id, description, journal_id, context)
        res['reference_type'] = invoice.reference_type
        return res

    def create(self, cr, uid, vals, context=None):
        partner_id = vals.get('partner_id')
        if not partner_id:
            raise orm.except_orm(_('Warning!'), _('Please fill in the Partner field.'))
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        partner = partner.commercial_partner_id  # replace by the partner for which the accounting entries will be created
        if vals.get('type'):
            inv_type = vals.get('type')
        else:
            inv_type = self._get_type(cr, uid, context=context)
            vals['type'] = inv_type
        reference_type = vals.get('reference_type')
        reference = vals.get('reference')
        if inv_type == 'out_invoice':
            reference_type = reference_type or partner.out_inv_comm_type or 'none'
            if not self.check_bbacomm(reference):
                reference = self.generate_bbacomm(cr, uid, [], inv_type, reference_type, partner_id, reference)['value']['reference']
        elif not reference_type:
            reference_type = 'none'

        if reference_type == 'bba':
            if not reference:
                raise orm.except_orm(_('Warning!'),
                    _('Empty BBA Structured Communication!' \
                      '\nPlease fill in a BBA Structured Communication.'))
            if self.check_bbacomm(reference):
                reference = re.sub('\D', '', reference)
                reference = '+++' + reference[0:3] + '/' + reference[3:7] + '/' + reference[7:] + '+++'
                if inv_type == 'out_invoice':
                    same_ids = self.search(cr, uid,
                        [('type', '=', 'out_invoice'), ('state', '!=', 'draft'),
                         ('reference_type', '=', 'bba'), ('reference', '=', reference)])
                    if same_ids:
                        reference_type, reference = self.duplicate_bba(cr, uid, inv_type, reference, partner)
        vals.update({'reference_type': reference_type, 'reference': reference})
        return super(account_invoice, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context={}):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for inv in self.browse(cr, uid, ids, context):
            if 'reference_type' in vals:
                reference_type = vals['reference_type']
            else:
                reference_type = inv.reference_type or ''
            if reference_type == 'bba':
                if 'reference' in vals:
                    bbacomm = vals['reference']
                else:
                    bbacomm = inv.reference or ''
                if self.check_bbacomm(bbacomm):
                    reference = re.sub('\D', '', bbacomm)
                    vals['reference'] = reference = '+++' + reference[0:3] + '/' + reference[3:7] + '/' + reference[7:] + '+++'
                    if inv.type == 'out_invoice':
                        same_ids = self.search(cr, uid,
                            [('id', '!=', inv.id), ('type', '=', 'out_invoice'), ('state', '!=', 'draft'),
                             ('reference_type', '=', 'bba'), ('reference', '=', reference)])
                        if same_ids:
                            partner = inv.partner_id.commercial_partner_id  # replace by the partner for which the accounting entries will be created
                            reference_type, reference = self.duplicate_bba(cr, uid, inv.type, reference, partner)
                            vals.update({'reference_type': reference_type, 'reference': reference})
        return super(account_invoice, self).write(cr, uid, ids, vals, context)

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        invoice = self.browse(cr, uid, id, context=context)
        if invoice.type in ['out_invoice']:
            reference_type = invoice.reference_type or 'none'
            default['reference_type'] = reference_type
            if reference_type == 'bba':
                partner = invoice.partner_id.commercial_partner_id  # replace by the partner for which the accounting entries will be created
                default['reference'] = self.generate_bbacomm(cr, uid, [],
                    invoice.type, reference_type,
                    partner.id, '', context=context)['value']['reference']
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

    _columns = {
        'reference': fields.char('Communication', size=64, help="The partner reference of this invoice."),
        'reference_type': fields.selection(_get_reference_type, 'Communication Type',
            required=True),
    }

    _constraints = [
        (_check_communication, 'Invalid BBA Structured Communication !', ['Communication']),
        ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
