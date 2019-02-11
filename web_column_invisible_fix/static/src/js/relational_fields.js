/* Copyright 2019 Noviat (www.noviat.com) */

odoo.define("web_column_invisible_fix.relational_fields", function (require) {
    "use strict";

    var relational_fields = require('web.relational_fields');

    relational_fields.FieldOne2Many.include({

        init: function () {
            var self = this;
            this._super.apply(this, arguments);
            var todo = false;
            var arch = this.view && this.view.arch;
            if (arch) {
                /* 
                Set columnInvisibleFields which have not been set before.
                This is the case for O2M fields where the tree view is not embedded in the form view.
                */
                if (typeof this.attrs.columnInvisibleFields === "undefined") {
                    this.attrs.columnInvisibleFields = {};
                    _.each(arch.children, function (child) {
                        if (child.attrs && child.attrs.modifiers && child.attrs.modifiers.column_invisible) {
                            self.attrs.columnInvisibleFields[child.attrs.name] = child.attrs.modifiers.column_invisible;
                            todo = true;
                        };
                    });
                };
            };
            if (todo) {
                this._processColumnInvisibleFields();
            };
        },
    });

});
