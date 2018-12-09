/*
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('account_bank_statement_advanced.reconcilation', function (require) {
    "use strict";

    var reconciliation = require('account.reconciliation');

    reconciliation.abstractReconciliationLine.include({

        start: function() {
            var self = this;
            var res = this._super();
            return $.when(res).then(function () {
                if (self.change_partner_field !== undefined) {
                    self.change_partner_field.field.domain = [['parent_id', '=', false]];
                };
            });
        },

    });

});
