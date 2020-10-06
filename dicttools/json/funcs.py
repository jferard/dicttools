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
from dataclasses import is_dataclass, fields, MISSING
from functools import reduce
from typing import Mapping, Sequence, Any, Iterable, Collection

from dicttools.common import is_plain_iterable, idx, stop_range_0
from dicttools.json.signature import *
from dicttools.types import K


def find(signature, data):
    """
    >>> list(find(Signature(any_key[:]), {"a": {"b": 1}}))
    [(['a', 'b'], 1)]
    >>> list(find(Signature(any_key[:1]), {"a": {"b": 1, "c": 2}}))
    [(['a'], {'b': 1, 'c': 2})]
    >>> list(find(Signature(any_key[:1], "b"), {"a": {"b": 1, "c": 2}}))
    [(['a', 'b'], 1)]
    >>> list(find(Signature(any_key[:], "b")[:], {"b": {"b": {"b": 2}}}))
    [(['b', 'b', 'b'], 2)]

    :param signature: the signature
    :param data: the data
    :yield: tuple (path, value)
    """

    def find_aux(sig, data, cur_path):
        if isinstance(data, Mapping):
            yield from find_in_dict(sig, data, cur_path)
        elif is_plain_iterable(data):
            yield from find_in_list(sig, data, cur_path)
        else:
            if sig.can_skip():
                yield cur_path, data

    def find_in_list(sig, data, cur_path):
        for i in range(len(data)):
            try:
                new_sig = sig.try_index(i)
            except IndexError:
                pass
            else:
                new_path = cur_path + [i]
                new_data = data[i]
                if new_sig:
                    yield from find_aux(new_sig, new_data, new_path)
                else:
                    yield new_path, new_data

    def find_in_dict(sig, data, cur_path):
        for k in list(data):
            try:
                new_sig = sig.try_key(k)
            except KeyError:
                pass
            else:
                #                    print(new_sig, k)
                new_path = cur_path + [k]
                new_data = data[k]
                if new_sig:
                    yield from find_aux(new_sig, new_data, new_path)
                else:
                    yield new_path, new_data

    yield from find_aux(signature, data, [])


def update(sig, data, f):
    """
    >>> update(Signature(any_key[:1]), {"a": {"b": 1}}, lambda _path, v: list(v))
    {'a': ['b']}
    >>> update(Signature(any_key[:1], "b"), {"a": {"b": 1, "c": 2}}, lambda _path, _v: None)
    {'a': {'c': 2}}

    :param sig:
    :param data:
    :param f:
    :return:
    """
    for path, v in find(sig, data):
        new_v = f(path, v)
        d = data
        *ks, k0 = path
        for k in ks:
            d = d[k]
        if new_v is None:
            del d[k0]
        else:
            d[k0] = new_v

    return data


def unlist(d, apply=idx):
    """
    Transform json lists into dicts

    >>> unlist({'a': ['b', 'c']})
    {'a': {idx(0): 'b', idx(1): 'c'}}
    >>> unlist({'a': ['b', 'c']}, None)
    {'a': {0: 'b', 1: 'c'}}
    >>> unlist({'a': ['b', 'c']}, str)
    {'a': {'0': 'b', '1': 'c'}}
    """

    def unlist_aux(data):
        if isinstance(data, Mapping):
            return {k: unlist_aux(v) for k, v in data.items()}
        elif is_plain_iterable(data):
            return {i: unlist_aux(v) for i, v in enumerate(data)}
        else:
            return data

    def unlist_aux_apply(data):
        if isinstance(data, Mapping):
            return {k: unlist_aux_apply(v) for k, v in data.items()}
        elif is_plain_iterable(data):
            return {apply(i): unlist_aux_apply(v) for i, v in enumerate(data)}
        else:
            return data

    if apply is None:
        return unlist_aux(d)
    else:
        return unlist_aux_apply(d)


def relist(d, accept=idx):
    """
    >>> relist({idx(0): 'a', idx(1):'b'})
    ['a', 'b']

    >>> relist({0: 'a', 1:'b'})
    {0: 'a', 1: 'b'}

    >>> relist({0: 'a', 1:'b'}, int)
    ['a', 'b']

    >>> relist({'0': 'a', '1':'b'}, str)
    ['a', 'b']

    >>> relist({'0': 'a', '2':'b'}, str)
    {'0': 'a', '2': 'b'}

    >>> relist({0: 'a', 2:'b'}, int)
    {0: 'a', 2: 'b'}

    :param d:
    :param accept: idx, int or str
    :return:
    """
    def relist_aux_idx(data):
        if isinstance(data, Mapping):
            stop = stop_idx(data)
            if stop == -1:
                return {k: relist_aux_idx(v) for k, v in data.items()}
            else:
                return [relist_aux_idx(data[idx(i)]) for i in range(stop)]
        elif is_plain_iterable(data):
            return [relist_aux_idx(v) for v in data]
        else:
            return data

    def stop_idx(data: Mapping):
        if all(isinstance(k, idx) for k in data):
            stop = stop_range_0([k.i for k in data])
            if stop == -1:
                raise ValueError(
                    f"The idx(...) should be consecutive "
                    f"and start at idx(0)")
            else:
                return stop
        elif any(isinstance(k, idx) for k in data):
            raise ValueError(f"Do not mix idx(...) and other keys")
        else:
            return -1

    def relist_aux_int(data):
        if isinstance(data, Mapping):
            stop = stop_int(data)
            if stop == -1:
                return {k: relist_aux_int(v) for k, v in data.items()}
            else:
                return [relist_aux_int(data[i]) for i in range(stop)]
        elif is_plain_iterable(data):
            return [relist_aux_int(v) for v in data]
        else:
            return data

    def stop_int(data: Mapping):
        if all(isinstance(v, int) for v in data):
            return stop_range_0(data)
        elif any(isinstance(v, int) for v in data):
            raise ValueError(f"Do not mix int indices and other keys")
        else:
            return -1

    def relist_aux_str(data):
        if isinstance(data, Mapping):
            stop = stop_str(data)
            if stop == -1:
                return {k: relist_aux_str(v) for k, v in data.items()}
            else:
                return [relist_aux_str(data[str(i)]) for i in range(stop)]
        elif is_plain_iterable(data):
            return [relist_aux_str(v) for v in data]
        else:
            return data

    def stop_str(data: Mapping):
        if all(isinstance(k, str) for k in data):
            return stop_range_0([int(k) for k in data])
        elif any(isinstance(v, str) for v in data):
            raise ValueError(f"Do not mix str indices and other keys")
        else:
            return -1

    if accept == idx:
        return relist_aux_idx(d)
    elif accept == str:
        return relist_aux_str(d)
    elif accept == int:
        return relist_aux_int(d)
    else:
        raise ValueError(
            "Parameter accept should be idx|int|str, not {}".format(accept))


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


def map_dict(d, func, default=None, only_terminal=True):
    def map_to_seq(d, default=None):
        m = max(d)
        return [d.get(i, default) for i in range(m)]

    def map_dict_only_terminal(parent, data, path):
        if isinstance(data, Mapping):
            return parent, dict(
                map_dict_only_terminal(k, v, path + [k]) for k, v in
                data.items())
        elif isinstance(data, Sequence) and not isinstance(data, str):
            return parent, map_to_seq(dict(
                map_dict_only_terminal(k, v, path + [i]) for i, v in
                enumerate(data)))
        else:
            return func(parent, data, path)

    def map_once(item, v, path):
        new_path = path + [item]
        _, data = map_dict_all(item, v, new_path)
        return func(item, data, new_path)

    def map_dict_all(parent, data, path):
        if isinstance(data, Mapping):
            return parent, dict(map_once(k, v, path) for k, v in data.items())
        elif isinstance(data, Sequence) and not isinstance(data, str):
            return parent, map_to_seq(
                dict(map_once(i, v, path) for i, v in enumerate(data)))
        else:
            return parent, data

    if only_terminal:
        return map_dict_only_terminal(None, d, [])[1]
    else:
        return map_dict_all(None, d, [])[1]


if __name__ == "__main__":
    import doctest

    doctest.testmod()


def recursive_items(d: Mapping[K, Any]):
    """
    >>> list(recursive_items({'b': 1, 'c': 2}))
    [('b', 1), ('c', 2)]
    >>> list(recursive_items({'a': {'b': 1, 'c': 2}, 'd': [{'e': 1}, 'f']}))
    [('a', 'b', 1), ('a', 'c', 2), ('d', idx(0), 'e', 1), ('d', idx(1), 'f')]

    :param d:
    :return:
    """
    if isinstance(d, Mapping):
        for k, v in d.items():
            for path in recursive_items(v):
                yield (k,) + path
    elif is_plain_iterable(d):
        for i, v in enumerate(d):
            for path in recursive_items(v):
                yield (idx(i),) + path
    else:
        yield (d,)


def recursive_dict(items: Iterable[Collection]) -> Mapping:
    """
    >>> recursive_dict([('b', 1), ('c', 2)])
    {'b': 1, 'c': 2}
    >>> recursive_dict([('a', 'b', 1), ('a', 'c', 2), ('d', idx(0), 'e', 1),
    ... ('d', idx(1), 'f')])
    {'a': {'b': 1, 'c': 2}, 'd': {idx(0): {'e': 1}, idx(1): 'f'}}
    >>> from json.funcs import relist
    >>> relist(_)
    {'a': {'b': 1, 'c': 2}, 'd': [{'e': 1}, 'f']}
    """
    def recursive_dict_aux(acc: Mapping, item: Collection):
        """
        Add an item to current mapping
        :param acc:
        :param item:
        :return:
        """
        k, *vs = item
        if not vs:
            raise ValueError(f"Path should have at least two elements: {item}")

        if len(vs) >= 2:
            if k in acc:
                value = recursive_dict_aux(acc[k], vs)
            else:
                value = recursive_dict_aux({}, vs)
        else:
            value = next(iter(vs))

        acc[k] = value

        return acc

    return reduce(lambda acc, item: recursive_dict_aux(acc, item), items, {})