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
from dataclasses import dataclass
from functools import reduce
from typing import (Mapping, Iterable, Collection, Iterator, MutableMapping,
                    Callable, Union, Any, Tuple)

from dicttools._util import (is_plain_iterable, json_item)
from dicttools.types import K


@dataclass(eq=True, order=True, unsafe_hash=True)
class idx:
    """
    >>> i = idx(10)
    >>> int(i)
    10
    """
    i: int

    def __repr__(self):
        return f"idx({self.i})"

    def __int__(self):
        return self.i


def to_canonical(d: Mapping, apply: Callable[[int], K] = idx):
    """
    Transform a JSON dict into a fully nested dict, without lists.

    >>> to_canonical({'a': ['b', 'c']})
    {'a': {idx(0): 'b', idx(1): 'c'}}

    :param d: a JSON mapping
    :param apply: a function that converts int indices to hashable keys
    :return: a fully nested mapping
    """
    if isinstance(d, Mapping):
        return {k: to_canonical(v, apply) for k, v in d.items()}
    elif is_plain_iterable(d):
        return {apply(i): to_canonical(v, apply) for i, v in enumerate(d)}
    else:
        return d


def to_json(d: Mapping,
            accept: Union[idx, int, str] = idx) -> Mapping:
    """
    Transform a fully nested dict into a JSON dict.

    >>> to_json({'a': {idx(0): 'b', idx(1): 'c'}})
    {'a': ['b', 'c']}

    :param d: a nested mapping
    :param accept: idx, int or str
    :return: a JSON dict
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
            try:
                return stop_range_0([int(k) for k in data])
            except ValueError:
                return -1
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


def nested_items(d_or_iter: Union[Mapping[K, Any], Iterator[Tuple[Tuple, Any]]]
                 ) -> Iterator[Tuple[Tuple, Any]]:
    """
    Create a generator over (path, value).

    >>> [item.draw() for item in nested_items({'b': 1, 'c': 2})]
    ['b^1', 'c^2']
    >>> [item.draw() for item in nested_items(
    ...     {'a': {'b': 1, 'c': 2}, 'd': [{'e': 1}, 'f']})]
    ['a-b^1', 'a-c^2', 'd-idx(1)^f', 'd-idx(0)-e^1']

    :param d: a nested or JSON mapping
    :return: an iterator over (path, value), where path is the full path
    """
    if isinstance(d_or_iter, Iterator):
        return d_or_iter

    stack = [json_item(tuple(), d_or_iter)]
    while stack:
        item = stack.pop()
        if item.is_mapping():
            for k, v in item.items():
                stack.insert(0, json_item(item.path + (k,), v))
        elif item.is_plain_iterable():
            for i, v in item.enumerate():
                stack.insert(0, json_item(item.path + (idx(i),), v))
        else:
            yield item


def nested_flatten(d: Mapping[K, Any]) -> Mapping[K, Any]:
    """
    Flatten a nested dict.

    >>> nested_flatten({'a': {'b': 1, 'c': 2}, 'd': [{'e': 1}, 'f']})
    {('a', 'b'): 1, ('a', 'c'): 2, ('d', idx(1)): 'f', ('d', idx(0), 'e'): 1}

    :param d: a nested or JSON mapping
    :return: a one level dictionary
    """
    return dict(map(tuple, nested_items(d)))


def nested_expand(items: Iterable[Collection]) -> Mapping:
    """
    >>> nested_expand([(('a', 'b'), 1), (('a', 'c'), 2),
    ... (('d', idx(0), 'e'), 1), (('d', idx(1)), 'f')])
    {'a': {'b': 1, 'c': 2}, 'd': {idx(0): {'e': 1}, idx(1): 'f'}}
    """

    def nested_expand_reduce_func(acc: MutableMapping, item: Collection):
        """
        Add an item to current mapping
        :param acc:
        :param item:
        :return:
        """
        path, v = item
        if not path:
            raise ValueError(f"Path should have at least two elements: {item}")

        head, *tail = path
        if tail:
            if head in acc:
                value = nested_expand_reduce_func(acc[head], (tail, v))
            else:
                value = nested_expand_reduce_func({}, (tail, v))
        else:
            value = v

        acc[head] = value

        return acc

    return reduce(lambda acc, item: nested_expand_reduce_func(acc, item), items,
                  {})


def stop_range_0(vs: Collection[int]):
    """
    >>> stop_range_0([0,2,1,3])
    4
    >>> stop_range_0([0,2])
    -1
    >>> stop_range_0([1,2])
    -1
    >>> stop_range_0([-1,0,1,2])
    -1

    :param vs:
    :return:
    """
    m = max(vs)
    if len(vs) == m + 1 and all(v in range(m + 1) for v in vs):
        return m + 1
    else:
        return -1


if __name__ == "__main__":
    import doctest

    doctest.testmod()
