.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

======================================
CODA Import - Handle Payment Card Cost
======================================

This Module splits CODA Transactions which contain Payment Card cost into two lines.

Online payments can result in the following CODA transaction:

|
| Amount: 86.51
| Partner Name: WORLDLINE
| Partner Account Number: 666000000483
| Transaction Type: 0 - Simple amount without detailed data; e.g. : an individual credit transfer (free of charges).
| Transaction Family: 04 - Cards
| Transaction Code: 50 - Credit after a payment at a terminal
| Transaction Category: 000 - Net amount
| Structured Communication Type:  -
| Payment Reference:
| Communication: R:128 MC 27992973 REM:0094245 F:          51175 30/12BRT:0000088,50EUR C:00001,99 N:NNNNNN******NNNN
|

When installing this module you can define a CODA mapping rule with the transaction signature
in order to detect such a transaction.
You need to specify the positions in the transaction free form 'Communication' for the transaction amount and cost.
You can also change the signature of the resulting cost transaction to
e.g. Transaction Code: 37 Costs and Transaction Family: 006 Various fees/commissions

The CODA parsing engine will split out the transaction amount and cost into two statement lines
with the same transaction reference.

This split will take place before the reconcile engine handles the statement lines.
You can as a consequence specify also mapping rules to automatically post the transaction cost to the appropriate cost account.
