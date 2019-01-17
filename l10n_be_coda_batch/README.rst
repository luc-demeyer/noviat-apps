.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================================================
Module to enable batch import of CODA bank statements
=====================================================

This module allows batch processing of CODA files.
The CODA files must be stored in a directory of the Odoo Server before the batch import.

A Log is created during the import in order to document import errors.
If errors have been detected, the Batch Import Log state is set to 'error'.
When all CODA Files have been imported correctly, the Batch Import Log state is set to 'done'.

The user can always redo the batch import until all errors have been cleared. 

As an alternative, the user can force the Batch Import Log state to 'done'
(e.g. when the errors have been circumvented via single CODA file import or manual encoding).
