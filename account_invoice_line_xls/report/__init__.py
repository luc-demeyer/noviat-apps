# -*- coding: utf-8 -*-

try:
    from . import invoice_line_xls
except ImportError:
    import logging
    logging.getLogger(__name__).warn(
        "report_xls not available in addons path")
