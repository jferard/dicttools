"""
These operations mimic the [set operations](
https://docs.python.org/3/library/stdtypes.html#set).

Every json dict is seen as a set of tuples `(path, terminal value)`.

The semantic of tests is the following: two pathes are equal if... they are
equal, but two terminal values are equal depending on a given user function.

Example: `{'a': {'b': 1}, 'c': 2}` and `{'a': {'b': 1, 'c': 2}}` produce the
tuples `(('a', 'b'), 1)` and `(('c'), 2)` for the first and the tuples
`(('a', 'b'), 1)` and `(('a', 'c'), 2)`. They share the path `('a', 'b')` and
`1 == 1` for the common equality, hence they are not disjoint.

The semantic of operations is the following: we use the operation on tuples
`(path, terminal value)`. If two paths are equal, then the user function
is applied to the both terminal values.

Example: the union of `{'a': 1}` and `{'a': 2}` with the operation
`lambda x, y: [x, y]` is `{a: [1, 2}` because there is one path `(a,)` and
two terminal values `1` and `2`.
"""

# coding: utf-8
#  DictTools. Provides functions and operations to handle, explore,
#     modify Python nested dicts, especially JSON-like data
#     Copyright (C) 2020 J. Férard <https://github.com/jferard>
#
#  This file is part of DictTools.
#
#  DictTools is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  DictTools is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
from typing import Mapping

from dicttools.common import is_plain_iterable


def isdisjoint(d1, d2, func=lambda v1, v2: v1 == v2):
    """
    Are `d1` and `d2` disjoint?

    >>> isdisjoint({'a': 1}, {'a': 2})
    True

    But:

    >>> isdisjoint({'a': 1}, {'a': 2}, lambda _v1, _v2: True)
    False

    :param d1: the first dict
    :param d2: the second dict
    :param func: a fun that returns if a value equals another
    :return: True if the two dicts have no (path, value) in common
    """
    if isinstance(d1, Mapping):
        if isinstance(d2, Mapping):
            common_keys = set(d1) & set(d2)
            if common_keys:
                return all(isdisjoint(d1[k], d2[k], func) for k in common_keys)
    elif is_plain_iterable(d1):
        if is_plain_iterable(d2):
            return all(isdisjoint(v1, v2) for v1, v2 in
                       zip(d1, d2))  # we don't care about overflow
    else:
        return not func(d1, d2)

    return True


def issubdict(d1, d2, func=lambda v1, v2: v1 == v2):
    """
    Is `d2` a subdict of `d1`?

    >>> issubdict({'a': 1, 'b': 2}, {'a': 1})
    True
    >>> issubdict({'a': 1}, {'a': 1, 'b': 2})
    False

    :param d1: the first dict
    :param d2: the second dict
    :param func: a fun that returns if a value equals another
    :return: if `d2 <= d1`
    """
    if isinstance(d1, Mapping):
        if isinstance(d2, Mapping):
            if set(d2) <= set(d1):
                return all(issubdict(d1[k], d2[k], func) for k in set(d2))
    elif is_plain_iterable(d1):
        if is_plain_iterable(d2):
            if len(d2) <= len(d1):
                return all(issubdict(v1, v2) for v1, v2 in
                           zip(d1, d2))  # we don't care about overflow
    else:
        return func(d1, d2)

    return False


def issuperdict(d1, d2, func=lambda v1, v2: v1 == v2):
    return issubdict(d2, d1, func)


def union(d1, d2, func=lambda v1, v2: [v1, v2]):
    """

    >>> union({'a': 1}, {'b': 2}) == {'a': 1, 'b': 2}
    True
    >>> union({'a': 1}, {'a': 2})
    {'a': [1, 2]}
    >>> union({'a': 1}, {'a': [2, 3]})
    {'a': [1, 2, 3]}
    >>> union({'a': 1}, {'a': {'b': 2}})
    {'a': [1, {'b': 2}]}
    >>> union({'a': 1}, {'a': 2}, lambda x, y: x - y)
    {'a': -1}
    >>> union({'a': 1}, {'a': {'b': 2}}, lambda x, y: x - y)
    {'a': [1, {'b': 2}]}
    """
    if isinstance(d1, Mapping):
        if isinstance(d2, Mapping):
            return {
                k: d1[k] if k not in d2
                else d2[k] if k not in d1
                else union(d1[k], d2[k], func)
                for k in set(d1) | set(d2)
            }
        elif is_plain_iterable(d2):
            return [d1] + d2
        else:
            return [d1, d2]
    elif is_plain_iterable(d1):
        if is_plain_iterable(d2):
            return d1 + d2
        else:
            return d1 + [d2]
    else:
        if isinstance(d2, Mapping):
            return [d1, d2]
        elif is_plain_iterable(d2):
            return [d1] + d2
        else:
            return func(d1, d2)


def intersection(d1, d2, func=lambda v1, v2: v1 if v1 == v2 else None):
    """

    >>> intersection({'a': 1}, {})
    {}
    >>> intersection({'a': 1}, {'b': 2})
    {}
    >>> intersection({'a': 1, 'b': 2}, {'b': 2, 'c': 3})
    {'b': 2}
    >>> intersection({'a': 1}, {'a': 2})
    {'a': None}
    >>> intersection({'a': 1}, {'a': 2}, lambda x, y: x + y)
    {'a': 3}
    """
    if isinstance(d1, Mapping) and isinstance(d2, Mapping):
        return {
            k: inter
            for k, inter in {
                k: intersection(d1[k], d2[k], func)
                for k in set(d1) & set(d2)
            }
            if inter is not None
        }
    elif is_plain_iterable(d1) and is_plain_iterable(d2):
        return [
            inter
            for inter in (
                intersection(x, y, func)
                for x, y in zip(d1, d2)
            )
            if inter is not None
        ]
    elif not (is_plain_iterable(d2) or isinstance(d2, Mapping)):
        return func(d1, d2)

    return None


def difference(d1, d2, func=lambda v1, v2: v1 - v2):
    pass


def symmetric_difference(d1, d2, func=lambda v1, v2: v1 == v2):
    return union(d1, d2) - intersection(d1, d2)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
