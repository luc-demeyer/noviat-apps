.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==========================
Web 'column_invisible' fix
==========================

The 'column_invisible' modifier doesn't work for O2M fields
where the tree view is not embedded in the form view.

We have created a PR (cf. https://github.com/odoo/odoo/pull/30982) which fixes this limitation.
Until this PR is merged by Odoo we recommend to install the web_column_invisible_fix module.
