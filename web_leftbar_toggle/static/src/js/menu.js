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
openerp.web.Menu.include({
    /**
     * Enable left menu to be toggled
     */
    show_nav_bar: function() {
        var nav_bar = $('.oe_leftbar');
        nav_bar.css('display', 'table-cell');
    },
    hide_nav_bar: function() {
        var nav_bar = $('.oe_leftbar');
        nav_bar.css('display', 'none');
    },
    bind_menu: function() {
        var self = this;
        self._super();
        var toggle_button = $(document.createElement('span'));
        toggle_button.append('&#9776;');
        toggle_button.css('color', 'white');
        toggle_button.css('float', 'left');
        toggle_button.css('cursor', 'pointer');
        toggle_button.css('padding-top', '5px');
        toggle_button.css('padding-right', '10px');
        toggle_button.click(function(e){
            e.stopImmediatePropagation();
            var nav_bar = $('.oe_leftbar');
            if (nav_bar.css('display') == 'none') {
                self.show_nav_bar();
            } else {
                self.hide_nav_bar();
            }
        });
        $('#oe_main_menu_placeholder').prepend(toggle_button);
    },
    menu_click: function(id, needaction) {
        var self = this;
        self._super(id, needaction);
        self.show_nav_bar();
    },
});