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