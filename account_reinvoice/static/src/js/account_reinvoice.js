/*
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
