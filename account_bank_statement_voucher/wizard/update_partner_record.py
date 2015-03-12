# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from base_iban.base_iban import _ref_iban, _format_iban
import logging
_logger = logging.getLogger(__name__)


class update_partner_record(orm.TransientModel):
    _name = 'update.partner.record'
    _description = 'update.partner.record'

    def _get_info(self, cr, uid, context=None):
        #_logger.warn('_get_info, context = %s', context)
        info = context.get('info')
        return info
        
    _columns = {
        'info': fields.text('Partner Record Update Details', readonly=True),
        'update_partner': fields.boolean('Update Partner', help="Uncheck to disable Partner Record update."),
    }
    _defaults = {
        'info': _get_info,
        'update_partner': 1,
    }
    
    def button_process(self, cr, uid, ids, context=None):
        stline_obj = self.pool.get('account.bank.statement.line')
        partner_bank_obj = self.pool.get('res.partner.bank')
        update_partner = self.read(cr, uid, ids[0], ['update_partner'])['update_partner']
        if update_partner:
            if context.get('partner_bank_unlink_ids'):
                partner_bank_obj.unlink(cr, uid, context['partner_bank_unlink_ids'])
            if context.get('partner_bank_create'):
                stline = stline_obj.browse(cr, uid, context['active_id'], context=context)
                feedback = update_partner_bank(self, cr, uid, stline.counterparty_bic, stline.counterparty_number, stline.partner_id.id, stline.counterparty_name)
                if feedback:
                    raise orm.except_orm(_('Error !'),
                            _('Partner Record Update failed: %s') % (feedback) )               
        context['update_partner_record'] = 'done'
        context['destroy_wizard_form'] = True
        return stline_obj.action_process(cr, uid, context['active_ids'], context=context)


def calc_iban_checksum(country, bban):
    bban = bban.replace(' ', '').upper() + country.upper() + '00'
    base = ''
    for c in bban:
        if c.isdigit():
            base += c
        else:
            base += str(ord(c) - ord('A') + 10)
    kk = 98 - int(base) % 97
    return str(kk).rjust(2, '0')

def check_bban(country, bban):
    if country == 'BE':
        try:
            int(bban)
        except:
            return False        
        if len(bban) != 12:
            return False
    return True

def check_iban(iban):
    """
    Check the IBAN number (logic partially based upon base_iban module, cf. is_iban_valid method)
    """
    iban = _format_iban(iban).lower()
    if iban[:2] not in _ref_iban:
        return False
    if len(iban) != len(_format_iban(_ref_iban[iban[:2]])):
        return False
    #the four first digits have to be shifted to the end
    iban = iban[4:] + iban[:4]
    #letters have to be transformed into numbers (a = 10, b = 11, ...)
    iban2 = ""
    for char in iban:
        if char.isalpha():
            iban2 += str(ord(char)-87)
        else:
            iban2 += char
    #iban is correct if modulo 97 == 1
    return int(iban2) % 97 == 1

def get_bank(self, cr, uid, bic, iban):

    country_obj = self.pool.get('res.country')   
    bank_obj = self.pool.get('res.bank')

    bank_id = False
    bank_name = False
    feedback = False   
    bank_country = iban[:2]
    try:
        bank_country_id = country_obj.search(cr, uid, [('code', '=', bank_country)])[0]
    except:
        feedback = _("\n        Bank lookup failed due to missing Country definition for Country Code '%s' !") \
            % (bank_country)
    else:
        if iban[:2] == 'BE' and 'code' in bank_obj.fields_get_keys(cr, uid):
            # To DO : extend for other countries
            bank_code = iban[4:7]
            if bic:
                bank_ids = bank_obj.search(cr, uid, [('bic', '=', bic), ('code', '=', bank_code), ('country', '=', bank_country_id)])
                if bank_ids:
                    bank_id = bank_ids[0]
                else:
                    bank_id = bank_obj.create(cr, uid, {
                        'name': bic,
                        'code': bank_code,
                        'bic': bic,
                        'country': bank_country_id,
                        })
            else:
                bank_ids = bank_obj.search(cr, uid, [('code', '=', bank_code), ('country', '=', bank_country_id)])
                if bank_ids:
                    bank_id = bank_ids[0]
                    bank_data = bank_obj.read(cr, uid, bank_id, fields=['bic', 'name'])
                    bic = bank_data['bic']
                    bank_name = bank_data['name']
                else:
                    country = country_obj.browse(cr, uid, bank_country_id)
                    feedback = _("\n        Bank lookup failed. Please define a Bank with Code '%s' and Country '%s' !") \
                        % (bank_code, country.name)
        else:
            if not bic: 
                feedback = _("\n        Bank lookup failed due to missing BIC in Bank Statement for IBAN '%s' !") \
                    % (iban)
            else:
                bank_ids = bank_obj.search(cr, uid, [('bic', '=', bic), ('country', '=', bank_country_id)])
                if not bank_ids:
                    bank_name = bic
                    bank_id = bank_obj.create(cr, uid, {
                        'name': bank_name,
                        'bic': bic,
                        'country': bank_country_id,
                        })
                else:
                   bank_id = bank_ids[0]                    

    return bank_id, bic, bank_name, feedback
                
def update_partner_bank(self, cr, uid, bic, iban, partner_id, counterparty_name):
    partner_bank_obj = self.pool.get('res.partner.bank')
    bank_id = False
    feedback = False
    if check_iban(iban):
        bank_id, bic, bank_name, feedback = get_bank(self, cr, uid, bic, iban)
        if not bank_id:
            return feedback
    else:
        bban = iban
        #convert belgian BBAN numbers to IBAN
        if check_bban('BE', bban):
            kk = calc_iban_checksum('BE', bban)
            iban = 'BE' + kk + bban
            bank_id, bic, bank_name, feedback = get_bank(self, cr, uid, bic, iban)
            if not bank_id:
                return feedback

    if bank_id:
        partner_bank_id = partner_bank_obj.create(cr, uid, {
            'partner_id': partner_id,
            'name': counterparty_name,
            'bank': bank_id,
            'state': 'iban',
            'bank_bic': bic,
            'bank_name': bank_name,            
            'acc_number': iban,
            })
    return feedback
