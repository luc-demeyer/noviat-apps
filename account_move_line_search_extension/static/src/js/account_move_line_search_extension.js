/*
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define('account_move_line_search_extension.amlse', function (require) {
    "use strict";

    var core = require('web.core');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var Model = require('web.DataModel');

    var QWeb = core.qweb;

    var amlseListSearchView = ListView.extend({

        init: function () {
            this._super.apply(this, arguments);
            this.current_account = null;
            this.current_analytic_account = null;
            this.current_partner = null;
            this.journals = [];
            this.current_journal = null;
            this.date_ranges = [];
            this.current_date_range = null;
            this.current_reconcile = null;
            this.current_amount = null;
            this.options.addable = false;
            this.set_render_dict();
        },

        start: function () {
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var d1, d2;
            this.$el.parent().prepend(QWeb.render('AccountMoveLineSearchExtension', self.render_dict));
            d1 = $.when(new Model('account.journal').query(['name']).all().then(function (result) {
                self.journals = result}));
            d2 = $.when(new Model('date.range').query(['name', 'date_start', 'date_end']).all().then(function (result) {
                self.date_ranges = result}));
            self.set_change_events();
            return $.when(tmp, d1, d2);
        },

        is_action_enabled: function (action) {
            /* remove 'Delete' from Sidebar */
            return action == 'delete' ? false : this._super.apply(this, arguments);
        },

        set_change_events: function () {
            var self = this;
            this.$el.parent().find('.oe_account_select_account').change(function () {
                self.current_account = this.value === '' ? null : this.value;
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_analytic_account').change(function () {
                self.current_analytic_account = this.value === '' ? null : this.value;
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_partner').change(function () {
                self.current_partner = this.value === '' ? null : this.value;
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_journal').change(function () {
                self.current_journal = this.value === '' ? null : parseInt(this.value);
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_date_range').change(function () {
                self.current_date_range = this.value === '' ? null : parseInt(this.value);
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_reconcile').change(function () {
                self.current_reconcile = this.value === '' ? null : this.value;
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
            this.$el.parent().find('.oe_account_select_amount').change(function () {
                self.current_amount = this.value === '' ? null : this.value;
                self.do_search(self.last_domain, self.last_context, self.last_group_by);
            });
        },

        set_render_dict: function () {
            /*
            Customise this function to modify the rendering dict for the qweb template.
            By default the action context is passed as rendering dict.
            */
            this.render_dict = this.dataset.get_context().__contexts[1];
        },

        do_search: function (domain, context, group_by, selection_field) {
            var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            var o;
            var date_start, date_end;

            var oesj = self.$el.parent().find('.oe_account_select_journal')
            oesj.children().remove().end();
            oesj.append(new Option('', ''));
            for (var i = 0; i < self.journals.length; i++) {
                o = new Option(self.journals[i].name, self.journals[i].id);
                if (self.journals[i].id === self.current_journal) {
                    $(o).attr('selected', true);
                };
                oesj.append(o);
            };

            var oesdr = self.$el.parent().find('.oe_account_select_date_range')
            oesdr.children().remove().end();
            oesdr.append(new Option('', ''));
            for (var i = 0; i < self.date_ranges.length; i++) {
                o = new Option(self.date_ranges[i].name, self.date_ranges[i].id);
                if (self.date_ranges[i].id === self.current_date_range) {
                    $(o).attr('selected', true);
                    date_start = self.date_ranges[i].date_start;
                    date_end = self.date_ranges[i].date_end;
                };
                oesdr.append(o);
            };

            return self.search_by_selection(date_start, date_end);
        },

        aml_search_domain: function (date_start, date_end) {
            var self = this;
            var domain = [];
            if (self.current_account) domain.push(['account_id.code', 'ilike', self.current_account]);
            /* TODO: analytic
            if (self.current_analytic_account) domain.push(['analytic_account_id', 'in', self.current_analytic_account]); //cf. def search
            */
            if (self.current_partner) domain.push(['partner_id.name', 'ilike', self.current_partner]);
            if (self.current_journal) domain.push(['journal_id', '=', self.current_journal]);
            if (self.current_date_range) domain.push('&', ['date', '>=', date_start], ['date', '<=', date_end]);
            if (self.current_reconcile) domain.push(['full_reconcile_id.name', '=ilike', self.current_reconcile]);
            if (self.current_amount) domain.push(['amount_search', '=', self.current_amount]);
            //_.each(domain, function(x) {console.log('amlse, aml_search_domain, domain_part = ', x)});
            return domain;
        },

        search_by_selection: function (date_start, date_end) {
            var self = this;
            var domain = self.aml_search_domain(date_start, date_end);
            return self.old_search(new data.CompoundDomain(self.last_domain, domain), self.last_context, self.last_group_by);
        },

    });

    core.view_registry.add('amlse', amlseListSearchView);

});
