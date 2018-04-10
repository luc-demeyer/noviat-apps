# -*- coding: utf-8 -*-
from . import models
from . import report
from . import wizards


def refine_tax_template_constraint(cr):
    """
    pre_init_hook:
    refine tax template constraint to allow
    duplicate names to support multiple chart templates
    on the same company.
    """
    cr.execute(
        "ALTER TABLE account_tax_template "
        "DROP CONSTRAINT IF EXISTS "
        "account_tax_template_name_company_uniq;"
        "ALTER TABLE account_tax_template "
        "ADD CONSTRAINT account_tax_template_name_company_uniq "
        "UNIQUE (name, company_id, type_tax_use, chart_template_id)")
