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
from typing import List, Optional

from abc import ABC, abstractmethod


class Occurrences(ABC):
    @abstractmethod
    def next(self) -> Optional["Occurrences"]:
        """
        Consume one occurrence

        :return: the next value of Occurrences or None if there is not
        """
        pass

    @abstractmethod
    def can_skip(self) -> bool:
        """
        :return: True if we can skip the next occurrence
        """
        pass


class Once(Occurrences):
    def next(self) -> Optional[Occurrences]:
        return None

    def can_skip(self) -> bool:
        return False

    def __repr__(self):
        return "[1:1]"


once_instance: Once = Once()


class AnyNumber(Occurrences):
    def next(self) -> Optional[Occurrences]:
        return self

    def can_skip(self) -> bool:
        return True

    def __repr__(self):
        return "[:]"


any_number_instance: AnyNumber = AnyNumber()


class AtLeastN(Occurrences):
    def __init__(self, n: int):
        assert n > 0
        self._n = n

    def next(self) -> Occurrences:
        return at_least(self._n - 1)

    def can_skip(self) -> bool:
        return False

    def __repr__(self):
        return f"[{self._n}:]"


at_least_instances: List[Optional[Occurrences]] = [any_number_instance] + [
    AtLeastN(i) for i in range(1, 10)]


def at_least(n):
    if n >= 10:
        return AtLeastN(n)
    else:
        return at_least_instances[n]


class AtMostN(Occurrences):
    instances: List[Occurrences] = None

    def __init__(self, n: int):
        assert n > 0
        self._n = n

    def next(self) -> Optional[Occurrences]:
        return at_most(self._n - 1)

    def can_skip(self) -> bool:
        return True

    def __repr__(self):
        return f"[:{self._n}]"


at_most_instances: List[Optional[Occurrences]] = [None] + [
    AtMostN(i) for i in range(1, 10)]


def at_most(n):
    if n >= 10:
        return AtMostN(n)
    else:
        return at_most_instances[n]


class BetweenMAndN(Occurrences):
    def __init__(self, m: int, n: int):
        assert n > m > 0
        self._m = m
        self._n = n

    def next(self) -> Optional[Occurrences]:
        if self._m > 1:
            return BetweenMAndN(self._m - 1, self._n - 1)
        elif self._m == 1:
            return AtMostN(self._n - 1)
        else:
            raise Exception()

    def can_skip(self) -> bool:
        return False

    def __repr__(self):
        return f"[{self._m}:{self._n}]"


class Exactly(Occurrences):
    def __init__(self, n: int):
        self._n = n

    def next(self) -> Optional[Occurrences]:
        return exactly(self._n - 1)

    def can_skip(self) -> bool:
        return False

    def __repr__(self):
        return f"[{self._n}:{self._n}]"


exactly_instances: List[Optional[Occurrences]] = [None] + [
    Exactly(i) for i in range(1, 10)]


def exactly(n):
    if n >= 10:
        return Exactly(n)
    else:
        return exactly_instances[n]


def occurrences(item):
    """
    Create an instance of occurrences

    >>> occurrences(slice(5, None))
    [5:]
    >>> occurrences(slice(None, 5))
    [:5]
    >>> occurrences(slice(5, 5))
    [5:5]
    >>> occurrences(slice(5, 10))
    [5:10]

    :param item: int or slice
    :return: an instance of Occurrences
    """
    if isinstance(item, slice):
        if item.step is not None:
            raise ValueError("step should be unspecified (or None)")
        if item.start is None:
            if item.stop is None:
                return any_number_instance
            elif item.stop < 1:
                raise ValueError("stop >= 1")
            else:
                return at_most(item.stop)
        elif item.stop is None:
            if item.start < 0:
                raise ValueError("start >= 0")
            else:
                return at_least(item.start)
        elif item.stop == item.start:
            return exactly(item.start)
        else:
            return BetweenMAndN(item.start, item.stop)
    elif isinstance(item, int):
        return exactly(item)
    else:
        raise TypeError(
            f"occurrences indices must be integers or slices, not {type(item)}")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
