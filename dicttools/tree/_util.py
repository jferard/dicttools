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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Mapping, Tuple, Hashable, Any, Iterable

from dicttools import Item
from dicttools._util import Item
from dicttools.json import JsonItem
from dicttools.types import Tree


def list_get(a_list: List, i: int):
    return a_list[i] if i < len(a_list) else None


@dataclass
class TreeItem(Item, ABC):
    """
    The result of a search in a tree
    """
    @property
    @abstractmethod
    def terminal(self) -> bool:
        pass

    def is_mapping(self):
        return isinstance(self.value, Mapping)

    def items(self):
        if isinstance(self.value, Mapping):
            return self.value.items()
        else:
            raise TypeError(f"Value {self.value} has no items")

    @abstractmethod
    def draw(self):
        pass

    def __iter__(self):
        return iter((self.path, self.value))


@dataclass
class TerminalTreeItem(TreeItem):
    @property
    def terminal(self) -> bool:
        return True

    def draw(self):
        return "-".join(map(str, self.path)) + "^" + str(self.value)


@dataclass
class NonTerminalTreeItem(TreeItem):
    @property
    def terminal(self) -> bool:
        return False

    def draw(self):
        return "-".join(map(str, self.path + (self.value,)))


def tree_item(path: Tuple[Hashable], value: Hashable) -> TreeItem:
    """
    Build a tree item

    >>> tree_item(('a', 'b'), None)
    TerminalTreeItem(path=('a', 'b'), value=None)
    >>> tree_item(('a', 'b'), {'c': None})
    NonTerminalTreeItem(path=('a', 'b'), value={'c': None})
    >>> tree_item(('a', 'b'), 1)
    Traceback (most recent call last):
        ...
    TypeError: Leaf ('a', 'b') shoud be mapped to None, not 1

    :param path: the path
    :param value: the value
    :return: a TreeItem
    """
    if isinstance(value, Mapping):
        return NonTerminalTreeItem(path, value)
    elif value is None:
        return TerminalTreeItem(path, value)
    else:
        raise TypeError(f"Leaf {path} shoud be mapped to None, not {value}")


def is_tree(d: Mapping) -> bool:
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


def tree_clone(t: Tree) -> Tree:
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
    stack = [(root, k, v) for k, v in t.items()]
    while stack:
        ret, k, v = stack.pop()
        if isinstance(v, Mapping):
            new_ret = ret.setdefault(k, {})
            for k2, v2 in v.items():
                stack.append((new_ret, k2, v2))
        elif v is None:
            ret[k] = None
        else:
            raise TypeError(f"Leaf {k} shoud be mapped to None, not {v}")
    return root


def to_tree(items: Iterable[TreeItem], bfs_order=False) -> Tree:
    """
    Convert `TreeItem`s to a `Tree`.

    >>> to_tree([TerminalTreeItem(('a', 'b'), 'c')])
    {'a': {'b': {'c': None}}}
    >>> to_tree([TerminalTreeItem(('a',), 'b')], True)
    Traceback (most recent call last):
    ...
    KeyError: 'a'
    >>> to_tree([NonTerminalTreeItem(tuple(), 'a'), NonTerminalTreeItem(('a',), 'b'), TerminalTreeItem(('a', 'b'), 'c')], True)
    {'a': {'b': {'c': None}}}

    :param items:       the items
    :param bfs_order:   raise an error if items are not in BFS order.
    :return:            a Tree
    :raises KeyError:   if `bfs_order` is True and the items are not in BFS
                        order.
    """
    ret = {}
    root = ret
    if bfs_order:
        for se in items:
            ret = root
            for k in se.path:
                ret = ret[k]
            if se.terminal:
                ret[se.value] = None
            else:
                ret[se.value] = {}
    else:
        for se in items:
            if se.terminal:
                ret = root
                for k in se.path:
                    ret = ret.setdefault(k, {})
                ret[se.value] = None
    return root


if __name__ == "__main__":
    import doctest
    doctest.testmod()
