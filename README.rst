|Build Status| |Code Coverage|

DictTools
=========

Copyright (C) J. Férard 2020

DictTools provides functions and operations to handle, explore, modify Python nested dicts, especially JSON-like data.
Under GPL v.3

Overview
--------
Work in progress...

Goal
----
Imagine you want to add 1 to every value of a dict:

.. code-block:: python3

    >>> d = {'a': 1, 'b': 2}
    >>> {k: v+1 for k, v in d.items()}
    {'a': 2, 'b': 3}

Good. Now try with:

.. code-block:: python3

    >>> d = {'a': {'c': 1} , 'b': [2, 3]}

Pretty hard, isn't it? List comprehension are almost useless with nested dicts. We need a more powerful tool.


.. |Build Status| image:: https://travis-ci.org/jferard/dicttools.svg?branch=master
   :target: https://travis-ci.org/jferard/dicttools
.. |Code Coverage| image:: https://img.shields.io/codecov/c/github/jferard/dicttools/master.svg
   :target: https://codecov.io/github/jferard/dicttools?branch=master
