Belgian Structured Communication for invoices
=============================================

This module adds support for the Belgian Structured Communication on in- and
outgoing invoices as follows:

    * The 'Reference' field label on an invoice is renamed to 'Communication'.
    * A Structured Communication can be generated automatically on outgoing
      invoices according to a number of algorithms.
    * The preferred type of Structured Communication and associated algorithm
      can be specified on the Partner records.
      A 'random' Structured Communication will be generated if no algorithm is
      specified on the Partner record.

Supported algorithms for outgoing invoices
------------------------------------------

    1) Random: **+++RRR/RRRR/RRRDD+++**

       **R..R** = Random Digits, **DD** = Check Digits

    2) Date: **+++DOY/YEAR/SSSDD+++**

       **DOY** = Day of the Year, **SSS** = Sequence Number, **DD** = Check Digits

    3) Customer Reference: **+++RRR/RRRR/SSSDDD+++**

       **R..R** = Customer Reference without non-numeric characters,
       **SSS** = Sequence Number, **DD** = Check Digits