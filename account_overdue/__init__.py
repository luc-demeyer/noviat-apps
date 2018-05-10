# -*- coding: utf-8 -*-
from . import models
from . import report
from . import wizard


def disable_action_report_print_overdue(cr):
    """
    pre_init_hook:
    disable Odoo Community overdue print
    """
    cr.execute(
        "UPDATE ir_values "
        "SET key2='#client_print_multi' "
        "WHERE name='Due Payments' "
        "AND model='res.partner' "
        "AND value LIKE 'ir.actions.report.xml,%' "
        "AND key2='client_print_multi';")
