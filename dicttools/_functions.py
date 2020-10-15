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
import sys
from typing import Mapping, Optional, Callable, List, Union, Iterable

from dicttools._types import K, HV, F, V


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


def to_data_class():
    pass


def dict_print(d: Mapping, stream=sys.stdout) -> str:
    """
        >>> dict_print({'A': {'B': {'D': {'G': None, 'H': None},
        ... 'E': {'I': {'J': None}}}, 'C': {'F': None}}})

        {'A': {'B': {'D': {'G': None,
                           'H': None},
                     'E': {'I': {'J': None}}},
               'C': {'F': None}}}
    """
    from pprint import pprint
    pprint(d, stream=stream, width=1)


def dataclass_from_dict(t, data, type_check=True):
    def process_field_value(field, data):
        value = get_field_value(field, data)
        try:
            return from_typing_collection(field.type, value)
        except AttributeError:
            return from_dict_aux(field.type, value)

    def get_field_value(field, data):
        try:
            return data[field.name]
        except KeyError:
            if field.default != MISSING:
                return field.default
            elif field.default_factory != MISSING:
                return field.default_factory()
            else:
                raise

    def from_typing_collection(t, data):
        origin, args = t.__origin__, t.__args__
        if issubclass(origin, Mapping):
            return {k: from_dict_aux(args[1], v) for k, v in data.items()}
        elif issubclass(origin, Sequence):
            return [from_dict_aux(args[0], x) for x in data]
        else:
            return data

    def from_dict_aux(t, data):
        assert isinstance(t, type), f"{t} should be a type"
        if is_dataclass(t):
            kwargs = {field.name: process_field_value(field, data)
                      for field in fields(t)}
            return t(**kwargs)
        else:
            if isinstance(data, t) or not type_check:
                return data
            else:
                raise TypeError(f"{repr(data)} is not an instance of {t}")

    return from_dict_aux(t, data)

if __name__ == "__main__":
    import doctest
    doctest.testmod()