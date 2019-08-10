/*
Copyright 2009-2019 Noviat.
License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('account_bank_statement_product_dimension.abs', function (require) {
    "use strict";

    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var ReconciliationRenderer = require('account.ReconciliationRenderer');
    var ReconciliationModel = require('account.ReconciliationModel');
    var _t = core._t;

    ReconciliationModel.StatementModel.include({

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.extra_field_names = ['product_id'];
            this.extra_fields = [{
                relation: 'product.product',
                type: 'many2one',
                name: 'product_id',
            }];
            this.extra_fieldInfo = {
                product_id: { string: _t("Product") },
            };
            this.quickCreateFields = this.quickCreateFields.concat(this.extra_field_names);
        },

        makeRecord: function (model, fields, fieldInfo) {
            var self = this;
            if (model === 'account.bank.statement.line' && fields.length === 6) {
                fields = fields.concat(this.extra_fields);
                _.extend(fieldInfo, this.extra_fieldInfo);
            };
            return this._super(model, fields, fieldInfo);
        },

        _formatToProcessReconciliation: function (line, prop) {
            var result = this._super(line, prop);
            if (prop.product_id) result.product_id = prop.product_id.id;
            return result;
        },

    });

    ReconciliationRenderer.LineRenderer.include({

        _renderCreate: function (state) {
            this._super(state);
            var record = this.model.get(this.handleCreateRecord);
            this.fields.product_id = new relational_fields.FieldMany2One(this,
                'product_id', record, { mode: 'edit' });
            this.fields.product_id.appendTo(this.$el.find('.create_product_id .o_td_field'));
        },

    });

});
