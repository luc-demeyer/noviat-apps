# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp.addons.base_iban.base_iban import _ref_iban, _format_iban


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
    Check the IBAN number
    Logic partially based upon base_iban module, cf. is_iban_valid method
    """
    iban = _format_iban(iban).lower()
    if iban[:2] not in _ref_iban:
        return False
    if len(iban) != len(_format_iban(_ref_iban[iban[:2]])):
        return False
    # the four first digits have to be shifted to the end
    iban = iban[4:] + iban[:4]
    # letters have to be transformed into numbers (a = 10, b = 11, ...)
    iban2 = ""
    for char in iban:
        if char.isalpha():
            iban2 += str(ord(char) - 87)
        else:
            iban2 += char
    # iban is correct if modulo 97 == 1
    return int(iban2) % 97 == 1


def get_iban_and_bban(number):
    """
    return IBAN and BBAN numbers
    Logic partially based upon base_iban module, cf. get_bban_from_iban method
    """
    mapping_list = {
        # TODO add rules for others countries
        'be': lambda x: x[4:],
        'fr': lambda x: x[14:],
        'ch': lambda x: x[9:],
        'gb': lambda x: x[14:],
    }

    number = number.replace(' ', '')
    for code, function in mapping_list.items():
        if number.lower().startswith(code):
            return [function(number), number]
    return [number]


def repl_special(s):
    s = s.replace("\'", "\'" + "'")
    return s


def str2date(date_str):
    try:
        return time.strftime('%Y-%m-%d', time.strptime(date_str, '%d%m%y'))
    except:
        return False


def str2time(time_str):
    return time_str[:2] + ':' + time_str[2:]


def str2float(str):
    try:
        return float(str)
    except:
        return 0.0


def list2float(lst):
            try:
                return str2float((lambda s: s[:-3] + '.' + s[-3:])(lst))
            except:
                return 0.0


def number2float(s, d):
    try:
        return float(s[:len(s) - d] + '.' + s[len(s) - d:])
    except:
        return False
