=====================
Invoice keep due date
=====================

Remove payment term when changing the due date manually
since otherwise the invoice 'validate' will recalculate
the due date and hence overwrite the manual change.