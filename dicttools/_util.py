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
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Tuple, Hashable, Any, Mapping, Iterable


@dataclass
class NestedItem(ABC):
    """
    The result of a search in a tree
    """
    path: Tuple[Hashable]
    value: Any

    @property
    @abstractmethod
    def terminal(self) -> bool:
        pass

    def is_mapping(self):
        return isinstance(self.value, Mapping)

    def items(self):
        return self.value.items()

    def is_plain_iterable(self):
        return is_plain_iterable(self.value)

    def enumerate(self):
        return enumerate(self.value)

    @abstractmethod
    def draw(self):
        pass

    def __iter__(self):
        return iter((self.path, self.value))


@dataclass
class TerminalItem(NestedItem):
    path: Tuple[Hashable]
    value: Any

    @property
    def terminal(self) -> bool:
        return True

    def draw(self):
        return "-".join(map(str, self.path)) + "^" + str(self.value)


@dataclass
class NonTerminalItem(NestedItem):
    path: Tuple[Hashable]
    value: Hashable

    @property
    def terminal(self) -> bool:
        return False

    def draw(self):
        return "-".join(map(str, self.path + (self.value,)))


def json_item(path: Tuple[Hashable], value: Any) -> NestedItem:
    if isinstance(value, Mapping) or is_plain_iterable(value):
        return NonTerminalItem(path, value)
    else:
        return TerminalItem(path, value)


def tree_item(path: Tuple[Hashable], value: Any) -> NestedItem:
    if isinstance(value, Mapping):
        return NonTerminalItem(path, value)
    else:
        return TerminalItem(path, value)


def is_plain_iterable(data):
    """
    :param data: the data
    :return: True if the data is a sequence, but not a string or a byte sequence
    """
    return isinstance(data, Iterable) and not isinstance(data, (str, bytes))