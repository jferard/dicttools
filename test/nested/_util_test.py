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

from dicttools.json import to_canonical, idx, to_json, nested_expand


class FuncsTest(unittest.TestCase):
    def test_to_nested(self):
        for expected, args in [
            ({'a': {0: 'b', 1: 'c'}}, ({'a': ['b', 'c']}, int)),
            ({'a': {'0': 'b', '1': 'c'}}, ({'a': ['b', 'c']}, str)),
        ]:
            self.assertEqual(to_canonical(*args), expected)

    def test_to_json(self):
        for expected, args in [
            ({'a': ['b', 'c']}, ({'a': {0: 'b', 1: 'c'}}, int)),
            ({'a': ['b', 'c']}, ({'a': {'0': 'b', '1': 'c'}}, str)),
            (['a', 'b'], ({idx(0): 'a', idx(1): 'b'},)),
            ({0: 'a', 1: 'b'}, ({0: 'a', 1: 'b'},)),
            (['a', 'b'], ({0: 'a', 1: 'b'}, int)),
            (['a', 'b'], ({'0': 'a', '1': 'b'}, str)),
            ({0: 'a', 2: 'b'}, ({0: 'a', 2: 'b'}, int)),
            ({'0': 'a', '2': 'b'}, ({'0': 'a', '2': 'b'}, str)),
            ({-1: 'a', 0: 'b', 1: 'c'}, ({-1: 'a', 0: 'b', 1: 'c'}, int)),
        ]:
            self.assertEqual(to_json(*args), expected)

    def test_nested_expand(self):
        for expected, items in [
            ({'b': 1, 'c': 2}, [(('b',), 1), (('c',), 2)])
        ]:
            self.assertEqual(nested_expand(items), expected)


if __name__ == '__main__':
    unittest.main()
