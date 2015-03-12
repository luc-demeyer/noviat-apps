Installation tips
=================

l10n_be_coa_multilang 6.0.1.6

1) Tax cases

Tax case templates have been added. 
If you are upgrading from a previous release you should add the following cases manually to your configuration and update the associated tax object:
- tax case: 48s44, tax object: VAT-OUT-00-EU-S
- tax case: 48s46L, tax object: VAT-OUT-00-EU-L
- tax case: 48s46T, tax object: VAT-OUT-00-EU-T

2) Tax objects

Tax templates have been added:
- VAT-OUT-21-CD2-S
- VAT-OUT-21-CD2-L
- VAT-OUT-21-INC-S
- VAT-OUT-21-INC-L
- VAT-IN-V82-21-CD2-S
- VAT-IN-V82-21-INC-S

You should add these manually to your configuration if you are upgrading from a previous release and if these tax objects are applicable to your business.



