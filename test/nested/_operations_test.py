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

import unittest
from dicttools.nested import union, isdisjoint, intersection


class TestDisjoint(unittest.TestCase):
    def test_list1(self):
        self.assertTrue(isdisjoint([1], [2]))

    def test_list2(self):
        self.assertTrue(isdisjoint([1, 2], [2, 3]))

    def test_list3(self):
        self.assertFalse(isdisjoint([1, 2], [1, 3]))

    def test_dict1(self):
        self.assertTrue(isdisjoint({'a': 1}, {'a': 2}))

    def test_dict_focus_on_keys(self):
        self.assertFalse(isdisjoint({'a': 1}, {'a': 2}, lambda _v1, _v2: True))

    def test_dict_rec1(self):
        self.assertTrue(isdisjoint({'a': {'b': 1}}, {'a': {'c': 1}}))

    def test_dict_rec2(self):
        self.assertFalse(isdisjoint({'a': {'b': 1}, 'c': 2}, {'a': {'b': 1, 'c': 2}}))

    def test_union(self):
        for expected, args in [
            ({'a': [1, 2]}, ({'a': 1}, {'a': 2})),
            ({'a': [1, 2, 3]}, ({'a': 1}, {'a': [2, 3]})),
            ({'a': [1, {'b': 2}]}, ({'a': 1}, {'a': {'b': 2}})),
            ({'a': -1}, ({'a': 1}, {'a': 2}, lambda x, y: x - y)),
            ({'a': [1, {'b': 2}]}, ({'a': 1}, {'a': {'b': 2}}, lambda x, y: x - y)),
        ]:
            self.assertEqual(union(*args), expected)

    def test_intersection(self):
        for expected, args in [
            ({}, ({'a': 1}, {})),
            ({}, ({'a': 1}, {'b': 2})),
        ]:
            self.assertEqual(intersection(*args), expected)


if __name__ == '__main__':
    unittest.main()
