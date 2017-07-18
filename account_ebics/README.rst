.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

EBICS banking protocol
======================

Implementation of the  EBICS banking protocol.

This module facilitates the exchange of files with banks via the EBICS protocol.

Installation
============

The module depends upon

- https://pypi.python.org/pypi/fintech
- https://pypi.python.org/pypi/cryptography

Configuration
=============

Go to **Settings > Users**

Add the users that are authorised to maintain the EBICS configuration to the 'EBICS Manager' Group.

Go to **Accounting > Configuration > Miscellaneous > EBICS Configuration**

Configure your EBICS configuration according to the contract with your bank.

Usage
=====

Go to **Accounting > Bank and Cash > EBICS file exchange**

EBICS Return Codes
------------------

During the processing of your EBICS upload/download, your bank may return an Error Code, e.g.

EBICS Functional Error:
EBICS_NO_DOWNLOAD_DATA_AVAILABLE (code: 90005)

A detailled explanation of the codes can be found on http://www.ebics.org.
You can also find this information in the doc folder of this module (file EBICS_Annex1_ReturnCodes).
