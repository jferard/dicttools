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

from typing import Mapping, Tuple, Hashable, Any, List, Iterable
from dataclasses import dataclass
from collections import Counter


@dataclass
class SearchItem:
    """
    The result of a search in a tree
    """
    path: Tuple[Hashable]
    value: Any
    terminal: bool

    def is_mapping(self):
        return isinstance(self.value, Mapping)

    def draw(self):
        if self.terminal:
            return "-".join(self.path) + "^" + str(self.value)
        else:
            return "-".join(self.path + (self.value,))


def tree_bfs(d):
    """
    >>> [se.draw() for se in tree_bfs({'a':{'b': 1, 'c':{'d':2}},
    ...     'e': 3, 'f':{'g':4, 'h':{'i': 5}}})]
    ['a', 'e', 'f', 'a-b', 'a-c', 'e^3', 'f-g', 'f-h', 'a-b^1', 'a-c-d', 'f-g^4', 'f-h-i', 'a-c-d^2', 'f-h-i^5']
    """
    for k in d.keys():
        yield SearchItem(tuple(), k, False)
    stack = [SearchItem((k,), v, not isinstance(v, Mapping)) for k, v in
             d.items()]
    while stack:
        se = stack.pop(0)
        if se.is_mapping():
            for k, v in se.value.items():
                yield SearchItem(se.path, k, False)
                stack.append(
                    SearchItem(se.path + (k,), v, not isinstance(v, Mapping)))
        else:
            yield se


def tree_dfs(d):
    """
    >>> [se.draw() for se in tree_dfs({'a':{'b': 1, 'c':{'d':2}}, 'e': 3, 'f':{'g':4, 'h':{'i': 5}}})]
    ['a', 'a-b', 'a-b^1', 'a-c', 'a-c-d', 'a-c-d^2', 'e', 'e^3', 'f', 'f-g', 'f-g^4', 'f-h', 'f-h-i', 'f-h-i^5']
    """
    for k, v in d.items():
        yield SearchItem(tuple(), k, False)
        stack = [SearchItem((k,), v, not isinstance(v, Mapping))]
        while stack:
            se = stack.pop()
            if se.is_mapping():
                temp = []
                for k, v in se.value.items():
                    temp.append(SearchItem(se.path, k, False))
                    temp.append(SearchItem(se.path + (k,), v,
                                           not isinstance(v, Mapping)))
                stack.extend(reversed(temp))
            else:
                yield se


def to_nested(ses: Iterable[SearchItem]):
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()