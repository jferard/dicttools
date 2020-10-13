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

from typing import Mapping, Callable, Iterator, Union

from dicttools._util import (is_plain_iterable)
from dicttools.json import (json_item, TerminalJsonItem, NonTerminalJsonItem,
                            reduce)
from dicttools._signature import Signature
from dicttools.json._util import idx, nested_items
from dicttools.types import Nested, NestedItem, Path


def nested_filter(func_or_signature: Union[Callable, Signature], d: Nested,
                  shortcut=False) -> Iterator[NestedItem]:
    """
    Filter a nested dict.

        filter(function or signature, d)


    >>> d = {'a':{'b': 1}, 'c':{'d':{'e':{'f': 2}, 'g': 3}}}
    >>> [item.draw() for item in nested_filter(lambda _: True, d)]
    ['a-b^1', 'c-d-g^3', 'c-d-e-f^2']
    >>> map_func = lambda item: len(item.path) == 2
    >>> [item.draw() for item in nested_filter(map_func, d)]
    ['a-b^1']
    >>> def map_func(item):
    ...     if len(item.path) < 2: return None
    ...     else: return len(item.path) == 2
    >>> [item.draw() for item in nested_filter(map_func, d, shortcut=True)]
    ['a-b^1', "c-d-{'e': {'f': 2}, 'g': 3}"]
    >>> def map_func(item):
    ...     if len(item.path) < 2: return None
    ...     else: return len(item.path) == 2 and item.terminal
    >>> [item.draw() for item in nested_filter(map_func, d, shortcut=True)]
    ['a-b^1']
    >>> from dicttools import any_key, any_of_keys
    >>> [item.draw() for item in
    ...     nested_filter(Signature(any_of_keys('a', 'c')), d)]
    ["a-{'b': 1}", "c-{'d': {'e': {'f': 2}, 'g': 3}}"]
    >>> [item.draw() for item in
    ...     nested_filter(Signature(any_of_keys('a', 'c'), 'd'), d)]
    ["c-d-{'e': {'f': 2}, 'g': 3}"]

    :param d: a nested dict
    :param func_or_signature: a function that takes a path and returns True
    if: 1. this path meets the condition; 2. a extension of this path may meet
    the condition
    """

    def nested_filter_signature(d: Nested, signature: Signature, cur_path
                                ) -> Iterator[NestedItem]:
        if isinstance(d, Mapping):
            for k, v in d.items():
                yield from nested_filter_signature_aux(k, v, signature,
                                                       cur_path)
        elif is_plain_iterable(d):
            for i, v in enumerate(d):
                k = idx(v)
                yield from nested_filter_signature_aux(k, v, signature,
                                                       cur_path)
        else:
            yield TerminalJsonItem(cur_path, d)

    def nested_filter_signature_aux(k, v, signature, cur_path):
        try:
            s = signature.take(k)
        except KeyError:
            pass
        else:
            path = cur_path + (k,)
            if s is not None:
                yield from nested_filter_signature(v, s, path)
            else:
                yield json_item(path, v)

    def nested_filter_shortcut_func(d: Nested, cur_path: Path) -> Iterator[
        NestedItem]:
        if isinstance(d, Mapping):
            item = NonTerminalJsonItem(cur_path, d)
            result = func_or_signature(item)
            if result is True:
                yield item
            elif result is None:
                for k, v in d.items():
                    next_path = cur_path + (k,)
                    yield from nested_filter_shortcut_func(v, next_path)
        elif is_plain_iterable(d):
            item = NonTerminalJsonItem(cur_path, d)
            result = func_or_signature(item)
            if result is True:
                yield item
            elif result is None:
                for i, v in enumerate(d):
                    next_path = cur_path + (idx(i),)
                    yield from nested_filter_shortcut_func(v, next_path)
        else:
            item = TerminalJsonItem(cur_path, d)
            if func_or_signature(item) is True:
                yield item

    def nested_filter_func(d: Nested) -> Iterator[NestedItem]:
        return filter(func_or_signature, nested_items(d))

    if isinstance(func_or_signature, Signature):
        yield from nested_filter_signature(d, func_or_signature, tuple())
    elif shortcut:
        yield from nested_filter_shortcut_func(d, tuple())
    else:
        yield from nested_filter_func(d)


def nested_map_values(d: Mapping, func):
    """
    Map the current dict.

    >>> d = {'a':{'b': 1}, 'c':{'d':{'e':{'f': 2}, 'g': 3}}}
    >>> [item.draw() for item in nested_map_values(d, lambda x: x+1)]
    ['a-b^2', 'c-d-g^4', 'c-d-e-f^3']

    :param d:
    :param func:
    :return:
    """
    return (item.map_value(func) for item in nested_items(d))


def nested_reduce_values(func, d: Mapping, initial=None):
    """
    Map the current dict.

    >>> d = {'a':{'b': 1}, 'c':{'d':{'e':{'f': 2}, 'g': 3}}}
    >>> nested_reduce_values(lambda acc, x: acc+x, d, 0)
    6

    :param d:
    :param func:
    :return:
    """
    if initial is None:
        return reduce(lambda acc, item: func(acc, item.value), nested_items(d))
    else:
        return reduce(lambda acc, item: func(acc, item.value), nested_items(d),
                      initial)


def nested_map(d: Mapping, func_or_signature, map_func, default=None,
               only_terminal=True):
    def map_to_seq(d, default=None):
        m = max(d)
        return [d.get(i, default) for i in range(m)]

    def map_dict_only_terminal(parent, data, path):
        if isinstance(data, Mapping):
            return parent, dict(
                map_dict_only_terminal(k, v, path + [k]) for k, v in
                data.items())
        elif is_plain_iterable(data):
            return parent, map_to_seq(dict(
                map_dict_only_terminal(k, v, path + [i]) for i, v in
                enumerate(data)))
        else:
            return map_func(parent, data, path)

    def map_once(item, v, path):
        new_path = path + [item]
        _, data = map_dict_all(item, v, new_path)
        return map_func(item, data, new_path)

    def map_dict_all(parent, data, path):
        if isinstance(data, Mapping):
            return parent, dict(map_once(k, v, path) for k, v in data.items())
        elif is_plain_iterable(data):
            return parent, map_to_seq(
                dict(map_once(i, v, path) for i, v in enumerate(data)))
        else:
            return parent, data

    if only_terminal:
        return map_dict_only_terminal(None, d, [])[1]
    else:
        return map_dict_all(None, d, [])[1]


def update(sig, data, f):
    """
    DEPRECATED: see nested_map

    >>> from dicttools import any_key
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
    DEPRECATED: see filter

    >>> from dicttools import any_key
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
                new_sig = sig.take(k)
            except KeyError:
                pass
            else:
                #                    print(new_sig, j)
                new_path = cur_path + [k]
                new_data = data[k]
                if new_sig:
                    yield from find_aux(new_sig, new_data, new_path)
                else:
                    yield new_path, new_data

    yield from find_aux(signature, data, [])


if __name__ == "__main__":
    import doctest

    doctest.testmod()
