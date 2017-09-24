.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Batch Reinvoice Service
=======================

This module allows to fully automate the Reinvoice process.

Configuration
=============

Go to **Settings > Technical > Automation > Scheduled Actions**

Activate the Reinvoice Service.

Usage
=====

| A Log is created during the batch process in order to document errors detected by the Reinvoice Service.
| Such errors will typically be caused by misconfigurations, e.g.

- Incomplete Journal Mapping Table
- Products not shared between companies or incorrectly defined

| If errors have been detected, the Reinvoice Log state is set to 'Error'.
| When all reinvoice entries in the accounting system have been processed correctly, the Reinvoice Log state is set to 'Done'.
| The user can force the Reinvoice Log state to 'Done' (e.g. when the errors have been resolved via the Manual Reinvoice process).
