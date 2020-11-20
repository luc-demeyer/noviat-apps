/*
# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/
odoo.define('account_bank_statement_advanced.ReconciliationModel', function (require) {
    "use strict";

    var ReconciliationModel = require('account.ReconciliationModel');

    ReconciliationModel.StatementModel.include({

        load: function (context) {
            if (context && context.statement_ids && context.st_line_ids) {
                context.statement_ids = context.statement_ids.concat(
                    context.st_line_ids.map(function (x) {return x * -1})
                );
            };
            return this._super(context);
        },

        loadData: function (ids, excluded_ids) {
            var context = this.context;
            if (context && context.st_line_ids) {
                ids = context.st_line_ids;
            };
            return this._super(ids, excluded_ids);
        },

    });

});
