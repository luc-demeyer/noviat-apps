from . import models


def update_bank_refs(cr):
    """
    pre_init_hook:
    update partner bank ir_model_data entries
    for migrations from 8.0 l10n_be_partner module
    """
    old = 'l10n_be_partner'
    new = 'l10n_be_partner_bank'
    model = 'res.bank'
    cr.execute(
        "UPDATE ir_model_data SET module = %s "
        "WHERE module = %s AND model = %s",
        (new, old, model))
