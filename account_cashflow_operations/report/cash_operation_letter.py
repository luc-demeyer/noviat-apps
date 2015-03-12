# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    
#    Copyright (c) 2012 Noviat nv/sa (www.noviat.be). All rights reserved.
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

import time
from report import report_sxw
from osv import osv

def nsplit(s, n):
    return [s[k:k+n] for k in range(0, len(s), n)]

class cash_operation_letter_print(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(cash_operation_letter_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'get_selection_label': self._get_selection_label,
            'format_bank': self._format_bank,            
        })

    def _get_selection_label(self, object, field, val):
        field_dict = self.pool.get(object._name).fields_get(self.cr, self.uid, fields=field, context={'lang': object.partner_lang})
        result_list = field_dict[field]['selection']
        result = filter(lambda x: x[0] == val, result_list)[0][1]
        return result
    
    def _format_bank(self, bank):
        result = ''
        if bank.iban:
            result = reduce(lambda x,y: x + ' ' + y, nsplit(bank.iban,4))
        elif bank.acc_number:
            result = bank.acc_number
        return result

report_sxw.report_sxw('report.cash.operation.letter.print',
                       'account.cash.operation', 
                       'addons/account_cashflow_operations/report/cash_operation_letter.mako',
                       parser=cash_operation_letter_print)
