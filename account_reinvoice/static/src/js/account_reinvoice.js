/*
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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
openerp.account_reinvoice = function (instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.web.account.bankStatementReconciliation.include({

        init: function(parent, context) {
            this._super.apply(this, arguments);

            this.create_form_fields['product_id'] = {
                id: "product_id",
                index: 5,
                label: _t("Product"),
                corresponding_property: "product_id",
                tabindex: 15,
                constructor: instance.web.form.FieldMany2One,
                field_properties: {
                    relation: "product.product",
                    string: _t("Product"),
                    type: "many2one",
                },
            };

            this.create_form_fields['reinvoice_key_id'] = {
                id: "reinvoice_key_id",
                index: 6,
                label: _t("Reinvoice Key"),
                corresponding_property: "reinvoice_key_id",
                tabindex: 15,
                constructor: instance.web.form.FieldMany2One,
                field_properties: {
                    relation: "account.reinvoice.key",
                    string: _t("Reinvoice Key"),
                    type: "many2one",
                },
            };

        },

    });

    instance.web.account.bankStatementReconciliationLine.include({

        prepareCreatedMoveLineForPersisting: function(line) {
            var dict = this._super.apply(this, arguments);
            if (line.product_id) dict['product_id'] = line.product_id;
            if (line.reinvoice_key_id) dict['reinvoice_key_id'] = line.reinvoice_key_id;
            return dict;
        },

    });

};
