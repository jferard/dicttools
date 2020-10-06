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

from dicttools import *

import unittest

from dicttools.json.signature import any_key, AnyKey


# class TestAny(unittest.TestCase):
#     def test_any_dict_consume(self):
#         a = any_key[:]
#         self.assertTrue(a.consume({}))
#
#     def test_any_dict_not_consume(self):
#         a = any_key[:]
#         self.assertFalse(a.consume(1))
#
#     def test_any_dict_consume_exception(self):
#         a = any_key[1:]
#         self.assertRaises(AnyException, lambda: a.consume(1))
#
#     def test_any_dict_not_consume_twice(self):
#         a = any_key[:1]
#         self.assertTrue(a.consume({}))
#         self.assertFalse(a.consume({}))
#
#     def test_full(self):
#         path = [1, any_key[:], 2]
#         actual_path = [1, {}, {}, 2]
#         for key in actual_path:
#             p0, *p = path
#             if key == p0:
#                 path = p
#             elif isinstance(p0, AnyKey):
#                 try:
#                     if p0.consume(key):
#                         path = p
#                 except AnyKey:
#                     raise
#
#         self.assertFalse(path)


if __name__ == '__main__':
    unittest.main()
