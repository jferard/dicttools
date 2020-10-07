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

from dataclasses import MISSING, is_dataclass, fields
from typing import Mapping, Sequence

from dicttools.nested._util import is_plain_iterable


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