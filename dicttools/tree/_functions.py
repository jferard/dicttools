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
from typing import (Mapping, Tuple, List, Iterator, Callable,
                    MutableMapping, Hashable)

from dicttools import Signature
from dicttools.tree._util import (list_get, TerminalTreeItem,
                                  NonTerminalTreeItem, tree_item, tree_clone,
                                  to_tree, TreeItem)
from dicttools._types import Tree, MutableTree


def tree_bfs(t: Tree) -> Iterator[TreeItem]:
    """
    >>> t = {'a': {'b': {1: None},
    ...            'c': {'d': {2: None}}},
    ...      'e': {3: None},
    ...      'f': {'g': {4: None},
    ...            'h': {'i': {5: None}}}}

    >>> [se.draw() for se in tree_bfs(t)]
    ['a', 'e', 'f', 'a-b', 'a-c', 'e^3', 'f-g', 'f-h', 'a-b^1', 'a-c-d', 'f-g^4', 'f-h-i', 'a-c-d^2', 'f-h-i^5']
    >>> to_tree(tree_bfs(t)) == t
    True

    :param t:   a Tree
    :return:    an iterator
    """
    for k in t.keys():
        yield NonTerminalTreeItem(tuple(), k)
    stack = [tree_item((k,), v) for k, v in t.items()]
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


def tree_dfs(t: Tree) -> Iterator[TreeItem]:
    """
    >>> t = {'a': {'b': {1: None},
    ...            'c': {'d': {2: None}}},
    ...      'e': {3: None},
    ...      'f': {'g': {4: None},
    ...            'h': {'i': {5: None}}}}

    >>> [se.draw() for se in tree_dfs(t)]
    ['a', 'a-b', 'a-b^1', 'a-c', 'a-c-d', 'a-c-d^2', 'e', 'e^3', 'f', 'f-g', 'f-g^4', 'f-h', 'f-h-i', 'f-h-i^5']
    >>> to_tree(tree_dfs(t)) == t
    True

    :param t:   a Tree
    :return:    an iterator
    """
    for k0, v0 in t.items():
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


def tree_height(t: Tree) -> int:
    """
    >>> tree_height({'a': None})
    0

    >>> t = {'a': {'b': {1: None},
    ...            'c': {'d': {2: None}}},
    ...      'e': {3: None},
    ...      'f': {'g': {4: None},
    ...            'h': {'i': {5: None}}}}

    >>> tree_height(t)
    3
    """
    if isinstance(t, Mapping):
        return 1 + max(tree_height(v) for v in t.values())
    elif t is None:
        return -1
    else:
        raise TypeError("Malformed Tree")


def tree_degree(t: Tree) -> int:
    """
    The number of children of a tree.

    >>> t = {'a': None, 'b': {3: None, 4: None}, 'c': None, 'd': {'e': None}}

    >>> tree_degree(t)
    4
    >>> tree_degree(t['b'])
    2

    :param t: a Tree
    :return: the number of children
    """
    if isinstance(t, Mapping):
        return len(t)
    elif t is None:
        return 0
    else:
        raise TypeError("Malformed Tree")


def tree_size(t: Tree) -> int:
    """
    The number of nodes in a tree.

    >>> t = {'a': None, 'b': {3: None, 4: None}, 'c': None, 'd': {'e': None}}

    >>> tree_size(t)
    7

    :param t: a Tree
    :return: the number of children
    """
    size = 0
    stack = [t]
    while stack:
        cur = stack.pop()
        if isinstance(cur, Mapping):
            size += len(cur)
            stack.extend(cur.values())
        elif cur is not None:
            raise TypeError(f"Malformed Tree {t}")
    return size


def tree_width(d: Tree) -> int:
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


def tree_from_binary(binary: List, start=1) -> Tree:
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


def tree_to_binary(t: Tree, start: int=1) -> List:
    """
    >>> tree = {'D': {'A': {'E': {'G': None, 'Q': None}, 'B': None}, 'F': {'R': {'V': None}, 'T': {'J': None, 'L': None}}}}
    >>> tree_to_binary(tree)
    [None, 'D', 'A', 'F', 'E', 'B', 'R', 'T', 'G', 'Q', None, None, 'V', None, 'J', 'L']

    :param d:
    :param start:
    :return:
    """
    if len(t) != 1:
        raise ValueError()
    k, v = next(iter(t.items()))
    stack = [(start, v)]
    binary_positions = [(start, k)]
    binary_len = start
    while stack:
        pos, cur = stack.pop()
        if cur is not None:
            children_pos = 2 * pos
            if children_pos + len(cur.items()) > binary_len:
                binary_len = children_pos + len(cur.items())

            for j, (k, v) in enumerate(cur.items()):
                binary_positions.append((children_pos + j, k))
                if v is not None:
                    stack.append((children_pos + j, v))

    binary = [None] * binary_len
    for pos, v in binary_positions:
        binary[pos] = v

    return binary


def tree_is_perfect(t: Tree) -> bool:
    pass


def tree_diameter(t: Tree) -> bool:
    """
    The longest path between two nodes of the tree (passing from child to
    parent is allowed).

    For this dict:

        >>> t = {'A': {'B': {'D': {'G': None, 'H': None},
        ... 'E': {'I': {'J': None}}}, 'C': {'F': None}}}

    The longest path is: J-I-E-B-D-G:

        >>> tree_diameter(t)
        5

    :param d:
    :return:
    """
    if t is None:
        return 0
    else:
        depth1 = 0
        depth2 = 0
        diameter = 0
        for k, v in t.items():
            depth_v = tree_height(v) + 1
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


def tree_length(tree: Tree) -> int:
    """
    >>> t = {'A': None}
    >>> tree_length(t)
    0
    >>> t = {'B': {'A': None}}
    >>> tree_length(t)
    1
    >>> t = {'I': {'B': {'A': None, 'R': None}}}
    >>> tree_length(t)
    5
    >>> t = {'I': {'B': {'A': None, 'R': None}, 'O':  {'M': {'R': None, 'E': None, 'T': None, 'F': None}}, 'N': None}}
    >>> tree_length(t)
    21

    :param d:
    :return:
    """

    def tree_length_aux(t: Tree, level: int) -> int:
        if t is None:
            return level - 1
        else:
            tl = level - 1
            for k, v in t.items():
                tl += tree_length_aux(v, level + 1)
            return tl

    return tree_length_aux(tree, 0) + 1


def tree_prune(tree: Tree, func_or_signature, maxprunes: int = -1) -> Iterator[
    Tuple[Tuple, Tree]]:
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

    def tree_prune_func(t: Tree, cur_path: Tuple[Hashable]
                        ) -> Iterator[Tuple[Tuple[Hashable], Tree]]:
        nonlocal maxprunes
        if maxprunes == 0:
            return

        if isinstance(t, Mapping):
            for k, v in t.items():
                next_path = cur_path + (k,)
                if func_or_signature(next_path):
                    t[k] = None
                    if maxprunes:
                        yield next_path, v
                        maxprunes -= 1
                    else:
                        break

                yield from tree_prune_func(v, next_path)

    def tree_prune_sig(t: Tree, sig: Signature, cur_path: Tuple[Hashable]
                       ) -> Iterator[Tuple[Tuple[Hashable], Tree]]:
        nonlocal maxprunes
        if maxprunes == 0:
            return

        if isinstance(t, Mapping):
            for k, v in t.items():
                if maxprunes:
                    try:
                        next_path = cur_path + (k,)
                        next_sig = sig.take(k)
                        if next_sig is None:
                            t[k] = None
                            yield next_path, v
                            maxprunes -= 1
                        else:
                            yield from tree_prune_sig(v, next_sig, next_path)
                    except KeyError:
                        pass

    if isinstance(func_or_signature, Callable):
        yield from tree_prune_func(tree, tuple())
    elif isinstance(func_or_signature, Signature):
        yield from tree_prune_sig(tree, func_or_signature, tuple())
    else:
        raise TypeError()


def tree_hook(tree1: MutableTree, func_or_signature, tree2: Tree,
              shallow: bool = True):
    """
    >>> d1 = {'a': {'b': None, 'c': {'d': None, 'e': None}}}
    >>> d2 = {'f': None}
    >>> tree_hook(d1, lambda path: path == ('a', 'b'), d2)
    ('a', 'b')
    >>> d1 == {'a': {'b': {'f': None}, 'c': {'d': None, 'e': None}}}
    True
    >>> tree_hook(d1, lambda path: path == ('a', 'x'), d2) is None
    True
    >>> d1 == {'a': {'b': {'f': None}, 'c': {'d': None, 'e': None}}}
    True
    """

    def tree_hook_sig(t: Tree):
        pass

    def tree_hook_func(t: MutableTree):
        stack = [(t, tuple())]
        while stack:
            cur, cur_path = stack.pop()
            if isinstance(cur, Mapping):
                for k, v in cur.items():
                    next_path = cur_path + (k,)
                    if func_or_signature(next_path):
                        if shallow:
                            cur[k] = tree2
                        else:
                            cur[k] = tree_clone(tree2)
                        return next_path
                    else:
                        stack.insert(0, (v, next_path))

    return tree_hook_func(tree1)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
