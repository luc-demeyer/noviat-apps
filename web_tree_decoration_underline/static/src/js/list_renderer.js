/* Copyright 2018-2019 Noviat (www.noviat.com) */

odoo.define("web_tree_decoration_underline.ListRenderer", function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        init: function () {
            this._super.apply(this, arguments);
            if ('decoration-uf' in this.arch.attrs) {
                var decoration_uf = py.parse(py.tokenize(this.arch.attrs['decoration-uf']));
                this.rowDecorations['decoration-uf'] = decoration_uf;
            };
        },
    });

});
