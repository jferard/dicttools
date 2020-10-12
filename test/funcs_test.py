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
from typing import List

import unittest

from dicttools.json.functions import update, nested_map
from dicttools.json._signature import Signature, any_of_keys, any_key


class TestFuncs(unittest.TestCase):
    def test(self):
        data = {0: {'a': 1, 'b': 2},
                1: {'a': 10, 'c': 13},
                2: {'a': 20, 'b': {'d': 100, 'e': 101}, 'c': 23},
                3: {'a': 30, 'b': 31, 'c': {'d': 300}}}
        update(Signature(any_key[:1], any_of_keys('b', 'c'), 'd'), data,
               lambda _path, v: f"f({v})")
        self.assertEqual(data, {0: {'a': 1, 'b': 2},
                                 1: {'a': 10, 'c': 13},
                                 2: {'a': 20, 'b': {'d': 'f(100)', 'e': 101},
                                     'c': 23},
                                 3: {'a': 30, 'b': 31, 'c': {'d': 'f(300)'}}})

    def test2(self):
        @dataclass
        class Point:
            x: int
            y: int = 0

        @dataclass
        class Polygon:
            ps: List[Point]

        p = Point(**{'x': 10, 'y': 20})

        @dataclass
        class A:
            def x(self):
                pass

    def test3(self):
        def f(k, v, p):
            if p and p[0] == 'a':
                ret = 'a_' + k, v
            elif p and p[-1] == 'c':
                ret = k, v + 10
            else:
                ret = k, v
            return ret

        """semantic from set operation: a dict is viewed as a set of tuples `(path, terminal value)`.
        """

        # print(nested_map({'a': {'b': 1}, 'b': {'c': 2}}, f, only_terminal=False))


if __name__ == "__main__":
    unittest.main()
