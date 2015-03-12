Installation tips
=================

1) Upgrade from account_coda 6.0.1.1

Upgrade instructions:
- Run account_coda upgrade
- Move Bank Account Number configuration parameters from the Bank Journals to the new 'CODA Bank Account Configuration' records
- Drop columns 'coda_st_naming' and 'coda_bank_acc' in table 'account_journal'
- Populate column 'coda_bank_account_id' in table 'coda_bank_statement'
