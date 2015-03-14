/*
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
*/

openerp.web_fix_binaryfile = function(instance) {

    instance.web.form.FieldBinaryFile.include({

        on_file_uploaded_and_valid : function (size, name, content_type, file_base64) {
            this.binary_value = true;
            this.set_filename(name); //Fix Noviat: set filename to get correct name in onchange
            this.internal_set_value(file_base64);
            var show_value = name + " (" + instance.web.human_size(size) + ")";
            this.$el.find('input').eq(0).val(show_value);
        },

    });

};
