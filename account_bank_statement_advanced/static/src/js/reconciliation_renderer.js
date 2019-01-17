/*
# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('account_bank_statement_advanced.ReconciliationRenderer', function (require) {
    "use strict";

    var ReconciliationRenderer = require('account.ReconciliationRenderer');

    ReconciliationRenderer.LineRenderer.include({

        _makePartnerRecord: function () {
            var self = this;
            return $.when(this._super.apply(this, arguments)).then(function (result) {
                self.model.localData[result].fieldsInfo.default.partner_id.domain = [["parent_id", "=", false]];
                return result;
            });
        },

    });

});
