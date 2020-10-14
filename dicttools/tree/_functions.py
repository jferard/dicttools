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
from collections import Counter
from typing import Mapping, Tuple, List, Iterable, Iterator, Callable

from dicttools import (Item)
from dicttools import Signature
from dicttools.tree._util import (list_get, TerminalTreeItem, NonTerminalTreeItem, tree_item)


def is_tree(d: Mapping):
    """
    A tree is represented by a nested dict. Leaves are keys mapped to `None`
    value.

    >>> is_tree(None)
    False
    >>> is_tree({'a': {'b': None, 'c': None}})
    True
    >>> is_tree({'a': {'b': None, 'c': 1}})
    False
    """
    if not isinstance(d, Mapping):
        return False

    stack = [d]
    while stack:
        cur = stack.pop()
        for k, v in cur.items():
            if v is None:
                continue
            elif isinstance(v, Mapping):
                stack.append(v)
            else:
                return False
    return True


def tree_bfs(d):
    """
    >>> d = {'a': {'b': {1: None},
    ...            'c': {'d': {2: None}}},
    ...      'e': {3: None},
    ...      'f': {'g': {4: None},
    ...            'h': {'i': {5: None}}}}

    >>> [se.draw() for se in tree_bfs(d)]
    ['a', 'e', 'f', 'a-b', 'a-c', 'e^3', 'f-g', 'f-h', 'a-b^1', 'a-c-d', 'f-g^4', 'f-h-i', 'a-c-d^2', 'f-h-i^5']
    """
    for k in d.keys():
        yield NonTerminalTreeItem(tuple(), k)
    stack = [tree_item((k,), v) for k, v in d.items()]
    while stack:
        se = stack.pop(0)
        if se.is_mapping():
            for k, v in se.value.items():
                if v is None:
                    yield TerminalTreeItem(se.path, k)
                else:
                    yield NonTerminalTreeItem(se.path, k)
                    stack.append(tree_item(se.path + (k,), v))
        else:
            yield se


def tree_clone(d: Mapping):
    """
    Clone a tree

    We have:

        >>> d1 = {'a': {'b': None, 'c': {'d': None, 'e': None}}}
        >>> d2 = d1
        >>> d2['a']['b'] = {'f': None}
        >>> d2 == d1
        True

    Because `d2` and `d1` refer to the same object. But:

        >>> d2 = tree_clone(d1)
        >>> d2 == d1
        True
        >>> d2['a']['b'] = None
        >>> d2 == d1
        False

    """
    root = {}
    stack = [(root, k, v) for k, v in d.items()]
    while stack:
        ret, k, v = stack.pop()
        if isinstance(v, Mapping):
            new_ret = ret.setdefault(k, {})
            for k2, v2 in v.items():
                stack.append((new_ret, k2, v2))
        else:
            ret[k] = None
    return root


def tree_dfs(d):
    """
    >>> [se.draw() for se in tree_dfs({'a':{'b': {1: None},
    ... 'c':{'d': {2: None}}}, 'e': {3: None}, 'f':{'g': {4: None},
    ... 'h':{'i': {5: None}}}})]
    ['a', 'a-b', 'a-b^1', 'a-c', 'a-c-d', 'a-c-d^2', 'e', 'e^3', 'f', 'f-g', 'f-g^4', 'f-h', 'f-h-i', 'f-h-i^5']
    """
    for k0, v0 in d.items():
        yield NonTerminalTreeItem(tuple(), k0)
        stack = [tree_item((k0,), v0)]
        while stack:
            se = stack.pop()
            if se.is_mapping():
                temp = []
                for k, v in se.value.items():
                    if v is None:
                        temp.append(TerminalTreeItem(se.path, k))
                    else:
                        temp.append(NonTerminalTreeItem(se.path, k))
                        temp.append(tree_item(se.path + (k,), v))
                stack.extend(reversed(temp))
            else:
                yield se


def to_nested(ses: Iterable[Item]):
    """
    >>> d = {'a':{'b': 1, 'c':{'d':2}}, 'e': 3, 'f':{'g':4, 'h':{'i': 5}}}
    >>> to_nested(tree_dfs(d)) == d
    True
    >>> to_nested(tree_bfs(d)) == d
    True
    """
    ret = {}
    root = ret
    for se in ses:
        if se.terminal:
            ret = root
            for k in se.path[:-1]:
                ret = ret.setdefault(k, {})
            ret[se.path[-1]] = se.value
    return root


def tree_depth(d: Mapping) -> int:
    """
    >>> d = {'a':{'b': 1, 'c':{'d':2}}, 'e': 3, 'f':{'g':4, 'h':{'i': 5}}}
    >>> tree_depth(d)
    3
    """
    if isinstance(d, Mapping):
        return 1 + max(tree_depth(v) for v in d.values())
    else:
        return 0


def tree_width(d: Mapping) -> int:
    """
    >>> d = {'a':{'b': 1, 'c':{'d':2}}, 'e': 3, 'f':{'g':4, 'h':{'i': 5}}}
    >>> tree_width(d)
    5
    """
    c = Counter()

    def _tree_width(d: Mapping, cur: int):
        """
        Update the counter
        :param d:
        :param cur:
        :return:
        """
        if isinstance(d, Mapping):
            c[cur] += len(d)
            for k, v in d.items():
                _tree_width(v, cur + 1)
        else:
            c[cur] += 1

    _tree_width(d, 0)
    return max(c.values())


def tree_from_binary(binary: List, start=1) -> Mapping:
    """
    >>> binary = [None, 'D', 'A', 'F', 'E', 'B', 'R', 'T', 'G', 'Q', None, None, 'V', None, 'J', 'L']
    >>> tree_from_binary(binary)
    {'D': {'A': {'E': {'G': None, 'Q': None}, 'B': None}, 'F': {'R': {'V': None}, 'T': {'J': None, 'L': None}}}}

    :param binary:
    :param start:
    :return:
    """
    stack = []
    positions = [start]
    while positions:
        pos = positions.pop()
        node = list_get(binary, pos)
        if node is not None:
            children_pos = pos * 2
            stack.append(
                (node,
                 list_get(binary, children_pos),
                 list_get(binary, children_pos + 1)
                 )
            )
            positions.append(children_pos)
            positions.append(children_pos + 1)

    new = []
    while stack:
        node, left, right = stack.pop()
        if left is None:
            if right is None:
                new.append(None)
            else:
                new.append({right: new.pop()})
        elif right is None:
            new.append({left: new.pop()})
        else:
            right_value = new.pop()
            left_value = new.pop()
            new.append({left: left_value, right: right_value})

    return {node: new.pop()}


def tree_to_binary(d, start=1) -> List:
    """
    >>> tree = {'D': {'A': {'E': {'G': None, 'Q': None}, 'B': None}, 'F': {'R': {'V': None}, 'T': {'J': None, 'L': None}}}}
    >>> tree_to_binary(tree)
    [None, 'D', 'A', 'F', 'E', 'B', 'R', 'T', 'G', 'Q', None, None, 'V', None, 'J', 'L']

    :param d:
    :param start:
    :return:
    """
    if len(d) != 1:
        raise ValueError()
    k, v = next(iter(d.items()))
    stack = [(start, v)]
    binary_positions = [(start, k)]
    binary_len = start
    while stack:
        pos, d = stack.pop()
        if d is not None:
            children_pos = 2 * pos
            if children_pos + len(d.items()) > binary_len:
                binary_len = children_pos + len(d.items())

            for j, (k, v) in enumerate(d.items()):
                binary_positions.append((children_pos + j, k))
                if v is not None:
                    stack.append((children_pos + j, v))

    binary = [None] * binary_len
    for pos, v in binary_positions:
        binary[pos] = v

    return binary


def tree_is_perfect(d) -> bool:
    pass


def tree_diameter(d) -> bool:
    """
    The longest path between two nodes of the tree (passing from child to
    parent is allowed).

    For this dict:

        >>> d = {'A': {'B': {'D': {'G': None, 'H': None},
        ... 'E': {'I': {'J': None}}}, 'C': {'F': None}}}

    The longest path is: J-I-E-B-D-G:

        >>> tree_diameter(d)
        5

    :param d:
    :return:
    """
    if d is None:
        return 0
    else:
        depth1 = 0
        depth2 = 0
        diameter = 0
        for k, v in d.items():
            depth_v = tree_depth(v)
            diameter_v = tree_diameter(v)
            if depth_v > depth1:
                depth1 = depth_v
            elif depth_v > depth2:
                depth2 = depth_v
            if diameter_v > diameter:
                diameter = diameter_v
        root_diameter = depth1 + 1 + depth2
        if root_diameter > diameter:
            diameter = root_diameter

        return diameter


def tree_length(d) -> bool:
    """
    >>> d = {'A': None}
    >>> tree_length(d)
    0
    >>> d = {'B': {'A': None}}
    >>> tree_length(d)
    1
    >>> d = {'I': {'B': {'A': None, 'R': None}}}
    >>> tree_length(d)
    5
    >>> d = {'I': {'B': {'A': None, 'R': None}, 'O':  {'M': {'R': None, 'E': None, 'T': None, 'F': None}}, 'N': None}}
    >>> tree_length(d)
    21

    :param d:
    :return:
    """

    def tree_length_aux(d, level):
        if d is None:
            return level - 1
        else:
            tl = level - 1
            for k, v in d.items():
                tl += tree_length_aux(v, level + 1)
            return tl

    return tree_length_aux(d, 0) + 1


def tree_prune(d: Mapping, func_or_signature, maxprunes: int = -1) -> Iterator[
    Tuple[Tuple, Mapping]]:
    """
    Split the dict at the current sig.

    >>> d = {'a': {'b': None,
    ...            'c': {'d': {'e': {'g': None,
    ...                              'h': {'i': None,
    ...                                    'j': None}}},
    ...                  'f': {'e': None}}}}
    >>> func = lambda path: path == ('a', 'c', 'd', 'e', 'h') or path == ('a', 'c', 'f')
    >>> list(tree_prune(d, func))
    [(('a', 'c', 'd', 'e', 'h'), {'i': None, 'j': None}), (('a', 'c', 'f'), {'e': None})]
    >>> d == {'a': {'b': None,
    ...             'c': {'d': {'e': {'g': None,
    ...                               'h': None}},
    ...                   'f': None}}}
    True
    >>> from dicttools import *
    >>> list(tree_prune(d, Signature(any_key[:2], any_of_keys('d', 'f'))))
    [(('a', 'c', 'd'), {'e': {'g': None, 'h': None}}), (('a', 'c', 'f'), None)]
    >>> from dicttools import dict_print
    >>> d == {'a': {'b': None,
    ...             'c': {'d': None,
    ...                   'f': None}}}
    True

    :param d:
    :param func_or_signature:
    :return:
    """
    def tree_prune_func(d1, cur_path):
        nonlocal maxprunes
        if maxprunes == 0:
            return

        if isinstance(d1, Mapping):
            for k, v in d1.items():
                next_path = cur_path + (k,)
                if func_or_signature(next_path):
                    d1[k] = None
                    if maxprunes:
                        yield next_path, v
                        maxprunes -= 1
                    else:
                        break

                yield from tree_prune_func(v, next_path)

    def tree_prune_sig(d1: Mapping, sig: Signature, cur_path: Tuple
                       ) -> Iterator[Tuple[Tuple, Mapping]]:
        nonlocal maxprunes
        if maxprunes == 0:
            return

        if isinstance(d1, Mapping):
            for k, v in d1.items():
                if maxprunes:
                    try:
                        next_path = cur_path + (k,)
                        next_sig = sig.take(k)
                        if next_sig is None:
                            d1[k] = None
                            yield next_path, v
                            maxprunes -= 1
                        else:
                            yield from tree_prune_sig(v, next_sig, next_path)
                    except KeyError:
                        pass

    if isinstance(func_or_signature, Callable):
        yield from tree_prune_func(d, tuple())
    elif isinstance(func_or_signature, Signature):
        yield from tree_prune_sig(d, func_or_signature, tuple())
    else:
        raise TypeError()


def tree_merge(d1, func_or_signature, d2) -> Mapping:
    """
    Merge `d1` and `d2` at level.

    :param d1:
    :param func_or_signature:
    :param d2:
    :return:
    """
    pass


if __name__ == "__main__":
    import doctest

    doctest.testmod()
