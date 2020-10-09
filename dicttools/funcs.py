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
from typing import Mapping, Optional, Callable, List, Union, Iterable

from dicttools.types import K, HV, F, V


def map_keys(func: Callable[[K], F], d: Mapping[K, V]) -> Mapping[F, V]:
    """
    >>> map_keys(str, {1:10, 2: 100})
    {'1': 10, '2': 100}

    :param d:
    :param func:
    :return:
    """
    return {func(k): v for k, v in d.items()}


def map_values(func: Callable[[V], F], d: Mapping[K, V]) -> Mapping[K, F]:
    """
    >>> map_values(str, {1:10, 2: 100})
    {1: '10', 2: '100'}

    :param d:
    :param func:
    :return:
    """
    return {k: func(v) for k, v in d.items()}


def reverse_dict(d: Mapping[K, HV],
                 func: Optional[Callable[[F, K], F]] = None,
                 initializer: Optional[Callable[[K], F]] = None
                 ) -> Union[Mapping[HV, F], Mapping[HV, List[K]]]:
    """
    >>> d = {'a': 1, 'b': 2, 'c': 1}
    >>> reverse_dict(d)
    {1: ['a', 'c'], 2: ['b']}
    >>> reverse_dict(d, func=lambda acc, j: acc+j)
    {1: 'ac', 2: 'b'}
    >>> d = {2: 'a', 4: 'b', 6: 'a'}
    >>> reverse_dict(d, func=lambda acc, j: acc*j, initializer=lambda j: 1)
    {'a': 12, 'b': 4}

    :param d:
    :param func:
    :param initializer:
    :return:
    """
    ret = {}
    if func is None:
        if initializer is None:
            for k, v in d.items():
                ret.setdefault(v, []).append(k)
        else:
            raise ValueError("Custom initializer requires a custom function")
    else:
        if initializer is None:
            for k, v in d.items():
                try:
                    ret[v] = func(ret[v], k)
                except KeyError:
                    ret[v] = k
        else:
            for k, v in d.items():
                try:
                    ret[v] = func(ret[v], k)
                except KeyError:
                    ret[v] = func(initializer(k), k)

    return ret


def reverse_multimap(d: Mapping[K, Iterable[HV]], fail_on_dup=False
                     ) -> Mapping[HV, K]:
    """
    >>> reverse_multimap({'a': [1, 2], 'b': [3]})
    {1: 'a', 2: 'a', 3: 'b'}
    >>> reverse_multimap({'a': [1, 2], 'b': [2]})
    {1: 'a', 2: 'b'}
    >>> reverse_multimap({'a': [1, 2], 'b': [2]}, True)
    Traceback (most recent call last):
        ...
    ValueError: Value 2 met twice

    :param d:
    :param fail_on_dup:
    :return:
    """
    if fail_on_dup:
        ret = {}
        for k, vs in d.items():
            for v in vs:
                if v in ret:
                    raise ValueError(f"Value {v} met twice")
                else:
                    ret[v] = k
        return ret
    else:
        return {v: k for k, vs in d.items() for v in vs}


def tree_from_refs(d):
    pass


def refs_from_tree(d):
    pass


def dfs(d):
    pass


def bfs(d):
    pass


def to_data_class():
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
