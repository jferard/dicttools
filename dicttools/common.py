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
from typing import Iterable, List, Collection


def is_plain_iterable(data):
    """
    :param data: the data
    :return: True if the data is a sequence, but not a string
    """
    return isinstance(data, Iterable) and not isinstance(data, str)


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


def stop_range_0(vs: Collection[int]):
    """
    >>> stop_range_0([0,2,1,3])
    4
    >>> stop_range_0([0,2])
    -1
    >>> stop_range_0([1,2])
    -1

    :param vs:
    :return:
    """
    m = max(vs)
    if len(vs) == m + 1 and all(v in range(m+1) for v in vs):
        return m+1
    else:
        return -1


if __name__ == "__main__":
    import doctest
    doctest.testmod()