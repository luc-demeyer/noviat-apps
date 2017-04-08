/*
# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
openerp.account_analytic_dimension_policy = function (instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;

    instance.web.account.bankStatementReconciliation.include({

        init: function(parent, context) {
            this._super.apply(this, arguments);
            this.model_account = new instance.web.Model("account.account");
            this.map_analytic_dimension_policy = {};
            var required_dict = {};
            _.each(this.create_form_fields, function(field) {                
                if (field['required']) {
                    required_dict[field['id']] = false;
                    };
                });
            /* 
            this.required_fields_set is used to check if all required fields 
            are filled in before showing the 'Ok' button on a line
            */
            this.required_fields_set = required_dict;
        },

        start: function() {
            var tmp = this._super.apply(this, arguments);
            var self = this;
            maps = [];
            maps.push(this.model_account
                .query(['id', 'analytic_dimension_policy'])
                .filter([['type', 'not in', ['view', 'consolidation', 'closed']]])
                .all().then(function(data) {
                    _.each(data, function(o) {
                        self.map_analytic_dimension_policy[o.id] = o.analytic_dimension_policy;
                        });
                })
            );
            return $.when(tmp, maps);
        },

    });

    instance.web.account.bankStatementReconciliationLine.include({

        init: function(parent, context) {
            this._super.apply(this, arguments);
            this.map_analytic_dimension_policy = this.getParent().map_analytic_dimension_policy;
            this.required_fields_set = this.getParent().required_fields_set;
            },

        UpdateRequiredFields: function(elt) {
            if (elt.get('value')) {
                this.required_fields_set[elt.name] = true;
            } else {
                this.required_fields_set[elt.name] = false;
            };
            var balanceChangedFlag = this.CheckRequiredFields(elt);
            if (balanceChangedFlag) {
                this.balanceChanged();      
            } else {
                if(this.st_line.has_no_partner)
                {
                    this.$(".button_ok").text("OK").removeClass("oe_highlight").attr("disabled", "disabled");
                }
                else
                {
                    this.$(".button_ok")
                        .text(_t("Keep open"))
                        .prop('disabled', false);
                }
            };
        },

        CheckRequiredFields: function() {
            var flag = _.every(this.required_fields_set);
            return flag;
        },

        formCreateInputChanged: function(elt, val) {
            this._super.apply(this, arguments);
            if (elt.name in this.required_fields_set) {
                this.UpdateRequiredFields(elt);
            };
        },

    });

};
