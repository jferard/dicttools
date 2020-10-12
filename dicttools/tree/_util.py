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
from typing import List, Mapping, Tuple, Hashable, Any

from dicttools._util import Item
from dicttools.json import JsonItem


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
class TerminalTreeItem(JsonItem):
    @property
    def terminal(self) -> bool:
        return True

    def draw(self):
        return "-".join(map(str, self.path)) + "^" + str(self.value)


@dataclass
class NonTerminalTreeItem(JsonItem):
    @property
    def terminal(self) -> bool:
        return False

    def draw(self):
        return "-".join(map(str, self.path + (self.value,)))


def tree_item(path: Tuple[Hashable], value: Any) -> JsonItem:
    if isinstance(value, Mapping):
        return NonTerminalTreeItem(path, value)
    else:
        return TerminalTreeItem(path, value)