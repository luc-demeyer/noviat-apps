.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

====================================
Control sending of automatic e-mails
====================================

This module allows to disable the automatic sending of e-mails
for a configurable set of models.

Configuration
=============

Define the system parameter 'mail_disable_auto_send' with the list of models
for which the automatic sending of e-mails will be disabled, e.g.
['sale.order', 'purchase.order', 'account.invoice']

Usage
=====

Examples:

1) Sales Order

When creating a new Sales Order the Salesperson (field 'user_id') receives by default
an e-mail message (create of object with mail_thread mixin results into a chatter
message with xml_id mail.mt_note.
Such a chatter messages generates an e-mail to internal followers (if the 'private' flag of
mail.mt_note is on it's default value which is 'True').

With this module installed and 'sale.order' included in the 'mail_disable_auto_send' models,
an e-mail will not be send to the Salesperson.
