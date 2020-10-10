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
from abc import ABC, abstractmethod
from copy import copy
from typing import (Callable, Any, Tuple, Sequence, Generic, TypeVar, Optional,
                    Union)

from dicttools.json._util import idx
from dicttools.json._occurrences import (Occurrences, once_instance,
                                         occurrences)

T = TypeVar('T')


class ItemMatches(Generic[T]):
    """
    As in shell, `ItemMatches` represents a chunk of a signature that can accept
    multiple values.

    >>> g = item_matches[lambda i: i==0 or i == '0', 1]
    >>> g.take(10)
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item 10'
    >>> g.take('0')
    """

    def __init__(self, func: Callable[[Any], bool], occurrences: Occurrences):
        self._func = func
        self._occurrences = occurrences

    def take(self, k: Any) -> Optional["ItemMatches"]:
        """
        Try to consume the key `k` and return the `ItemMatches` after the key was
        accepted, or None.

        :param k: the key to test
        :return: a new instance of `ItemMatches`
        :raise: KeyError if the key was not accepted
        """
        if self._func(k):
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                ret = ItemMatches(self._func, o)
                ret.__class__ = self.__class__
                for k, v in self.__dict__.items():
                    if k not in {"_func", "_occurrences"}:
                        ret.__dict__[k] = v
                return ret
        else:
            raise KeyError(f"Unexpected item {repr(k)}")

    def can_skip(self) -> bool:
        """
        :return: True if this `ItemMatches` can be skipped.
        """
        return self._occurrences.can_skip()


G = TypeVar('G', bound=ItemMatches)

Chunk = Union[Any, ItemMatches]


class AnyItem(ItemMatches):
    """
    Key or index

    >>> g = any_item[:2]
    >>> g = g.take(1)
    >>> g
    any_item[1:1]
    >>> g.take("abc") is None
    True
    """
    def __init__(self, occurrences: Occurrences = once_instance):
        ItemMatches.__init__(self, lambda k: True, occurrences)

    def _create(self, o: Occurrences) -> "AnyItem":
        return AnyItem(o)

    def __repr__(self):
        return f"any_item[{self._occurrences}]"


class ItemIn(ItemMatches):
    """
    >>> g = any_of_items[{'a', 'b', 'c'},:2]
    >>> g.take('d')
    Traceback (most recent call last):
    ...
    KeyError: "Unexpected item 'd'"
    >>> g = g.take('a')
    >>> g
    any_of_items[['a', 'b', 'c'], 1:1]
    >>> g.take('b') is None
    True
    """

    def __init__(self, vs: Sequence[Any],
                 occurrences: Occurrences = once_instance):
        ItemMatches.__init__(self, lambda k: k in vs, occurrences)
        self._vs = vs

    def __repr__(self):
        return f"any_of_items[{sorted(self._vs)}, {self._occurrences}]"


class ItemNotIn(ItemMatches):
    """
    >>> g = none_of_items[{'a', 'b', 'c'},:2]
    >>> g.take('a')
    Traceback (most recent call last):
    ...
    KeyError: "Unexpected item 'a'"
    >>> g = g.take('d')
    >>> g
    none_of_items[['a', 'b', 'c'], 1:1]
    >>> g.take('d') is None
    True
    """
    def __init__(self, vs, occurrences=once_instance):
        ItemMatches.__init__(self, lambda k: k not in vs, occurrences)
        self._vs = vs

    def __repr__(self):
        return f"none_of_items[{sorted(self._vs)}, {self._occurrences}]"


class KeyMatches(ItemMatches):
    """
    Key

    >>> g = key_matches[lambda k: k == 'a', 1]
    >>> g.take(1)
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item 1'
    >>> g.take('a') is None
    True
    """
    def __init__(self, func: Callable[[Any], bool],
                 occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: not isinstance(k, idx) and func(k),
                             occurrences)
        self._func_name = func.__name__

    def __repr__(self):
        return f"key_matches[{self._func_name}, {self._occurrences}]"


class AnyKey(ItemMatches):
    """
    Key

    >>> g = any_key[2]
    >>> g.take(1)
    any_key[1:1]
    >>> g.take(idx(1))
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item idx(1)'
    """
    def __init__(self, occurrences=once_instance):
        ItemMatches.__init__(self, lambda k: not isinstance(k, idx),
                             occurrences)

    def __repr__(self):
        return f"any_key[{self._occurrences}]"


class KeyIn(ItemMatches):
    """
    >>> g = any_of_keys[{'a', 'b', 'c'},:2]
    >>> g.take('d')
    Traceback (most recent call last):
    ...
    KeyError: "Unexpected item 'd'"
    >>> g = g.take('a')
    >>> g
    any_of_keys[['a', 'b', 'c'], 1:1]
    >>> g.take('b') is None
    True
    >>> g = any_of_keys[{0, 1, 2},:2]
    >>> g.take(idx(0))
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item idx(0)'
    >>> g = any_of_keys[{idx(0)},:2]
    Traceback (most recent call last):
    ...
    ValueError: Possible key must no be `idx`: {idx(0)}
    """
    def __init__(self, ks, occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: not isinstance(k, idx) and k in ks,
                             occurrences)
        self._ks = ks

    def __repr__(self):
        return f"any_of_keys[{sorted(self._ks)}, {self._occurrences}]"


class KeyNotIn(ItemMatches):
    """
    >>> g = none_of_keys[{'a', 'b', 'c'},:2]
    >>> g.take('a')
    Traceback (most recent call last):
    ...
    KeyError: "Unexpected item 'a'"
    >>> g = g.take('d')
    >>> g
    none_of_keys[['a', 'b', 'c'], 1:1]
    >>> g.take('d') is None
    True
    """
    def __init__(self, ks, occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: not isinstance(k, idx) and k not in ks,
                             occurrences)
        self._ks = ks

    def __repr__(self):
        return f"none_of_keys[{sorted(self._ks)}, {self._occurrences}]"


class IndexMatches(ItemMatches):
    """
    Key

    >>> g = index_matches[lambda k: k == 'a', 1]
    >>> g.take(1)
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item 1'
    >>> g.take('a') is None
    True
    """
    def __init__(self, func: Callable[[Any], bool],
                 occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: not isinstance(k, idx) and func(k),
                             occurrences)
        self._func_name = func.__name__

    def __repr__(self):
        return f"index_matches[{self._func_name}, {self._occurrences}]"


class AnyIndex(ItemMatches):
    """
    Key

    >>> g = any_index[2]
    >>> g.take(idx(1))
    any_index[1:1]
    >>> g.take(1)
    Traceback (most recent call last):
    ...
    KeyError: 'Unexpected item 1'
    """
    def __init__(self, occurrences=once_instance):
        ItemMatches.__init__(self, lambda k: isinstance(k, idx),
                             occurrences)

    def __repr__(self):
        return f"any_index[{self._occurrences}]"


class IndexIn(ItemMatches):
    """
    >>> g = any_of_indices[{'a', 'b', 'c'},:2]
    Traceback (most recent call last):
    ...
    ValueError: Possible key must no be `idx`: ['a', 'b', 'c']
    >>> g = any_of_indices[{0, 1, 2},:2]
    Traceback (most recent call last):
    ...
    ValueError: Possible key must no be `idx`: [0, 1, 2]
    >>> g = any_of_indices[{idx(0)},:2]
    >>> g.take(idx(0))
    any_of_indices[[idx(0)], 1:1]
    """
    def __init__(self, ks, occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: isinstance(k, idx) and k in ks,
                             occurrences)
        self._ks = ks

    def __repr__(self):
        return f"any_of_indices[{sorted(self._ks)}, {self._occurrences}]"


class IndexNotIn(ItemMatches):
    """
    >>> g = none_of_indices[{idx(0), idx(1), idx(2)},:2]
    >>> g.take('a')
    Traceback (most recent call last):
    ...
    KeyError: "Unexpected item 'a'"
    >>> g = g.take(idx(3))
    >>> g
    none_of_indices[[idx(0), idx(1), idx(2)], 1:1]
    >>> g.take(idx(4)) is None
    True
    """
    def __init__(self, ks, occurrences=once_instance):
        ItemMatches.__init__(self,
                             lambda k: isinstance(k, idx) and k not in ks,
                             occurrences)
        self._ks = ks

    def __repr__(self):
        return f"none_of_indices[{sorted(self._ks)}, {self._occurrences}]"


############
# builders #
############
class ItemMatchesBuilder:
    def __getitem__(self, item: Tuple[
        Callable[[Any], bool], Union[slice, int]]) -> ItemMatches:
        func, n = item
        return ItemMatches(func, occurrences(n))


class AnyItemBuilder:
    def __getitem__(self, item: Union[range, int]) -> AnyItem:
        """
        :param item: int or slice
        :return:
        """
        return AnyItem(occurrences(item))


class ItemInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> ItemIn:
        vs, n = item
        return ItemIn(vs, occurrences(n))


class ItemNotInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> ItemNotIn:
        vs, n = item
        return ItemNotIn(vs, occurrences(n))


class KeyMatchesBuilder:
    def __getitem__(self, item: Tuple[
        Callable[[Any], bool], Union[slice, int]]) -> ItemMatches:
        func, n = item
        return KeyMatches(func, occurrences(n))


class AnyKeyBuilder:
    def __getitem__(self, item: Union[range, int]) -> AnyKey:
        """
        :param item: int or slice
        :return:
        """
        return AnyKey(occurrences(item))


class KeyInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> KeyIn:
        ks, n = item
        if any(isinstance(k, idx) for k in ks):
            raise ValueError(f"Possible key must no be `idx`: {ks}")
        return KeyIn(ks, occurrences(n))


class KeyNotInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> KeyIn:
        ks, n = item
        return KeyNotIn(ks, occurrences(n))


class IndexMatchesBuilder:
    def __getitem__(self, item: Tuple[
        Callable[[Any], bool], Union[slice, int]]) -> ItemMatches:
        func, n = item
        return IndexMatches(func, occurrences(n))



class AnyIndexBuilder:
    def __getitem__(self, item: Union[range, int]) -> AnyIndex:
        """
        :param item: int or slice
        :return:
        """
        return AnyIndex(occurrences(item))


class IndexInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> IndexIn:
        ks, n = item
        if any(not isinstance(k, idx) for k in ks):
            raise ValueError(f"Possible key must no be `idx`: {sorted(ks)}")
        return IndexIn(ks, occurrences(n))


class IndexNotInBuilder:
    def __getitem__(self,
                    item: Tuple[Sequence[Any], Union[range, int]]) -> IndexIn:
        ks, n = item
        return IndexNotIn(ks, occurrences(n))

###########
# indices #
###########


class Signature(ItemMatches):
    """
    >>> Signature(any_key[:]).take("a")
    Signature([any_key[:]], 1:1)
    >>> Signature("b").take("b") is None
    True
    >>> Signature("b").take("c")
    Traceback (most recent call last):
    ...
    KeyError: 'b vs c'
    """

    def __init__(self, *chunks: Chunk, **kwargs):
        self._chunks = chunks
        try:
            self._occurrences = kwargs["occurrences"]
        except KeyError:
            self._occurrences = once_instance

    def take(self, k: Any) -> Optional["Signature"]:
        if not self._chunks:
            return None

        c0, *cs = self._chunks
        if c0 == k:
            if cs:
                return Signature(*cs)
            else:
                return None
        else:
            try:
                return self._try_key_glob(c0, cs, k)
            except AttributeError:
                raise KeyError(f"{c0} vs {k}")

    def _try_key_glob(self, c0: Chunk, cs: Tuple[Chunk], k: Any
                      ) -> Optional["Signature"]:
        try:
            c0 = c0.take(k)
        except KeyError:
            if c0.can_skip():
                return Signature(*cs).take(k)
            else:
                raise
        else:
            if c0 is None:
                if cs:
                    return Signature(*cs, occurrences=self._occurrences)
                else:
                    return None
            else:
                return Signature(c0, *cs, occurrences=self._occurrences)

    def can_skip(self) -> bool:
        if self._occurrences.can_skip():
            return True
        try:
            return all(c.can_skip() for c in self._chunks)
        except AttributeError:
            return False

    def __getitem__(self, item):
        return Signature(*self._chunks, occurrences=occurrences(item))

    def __repr__(self):
        chunks = ", ".join(str(c) for c in self._chunks)
        return f"Signature({sorted(self._chunks)}, {self._occurrences})"


def signature(*chunks):
    return Signature(chunks)


item_matches = ItemMatchesBuilder()
any_item = AnyItemBuilder()
any_of_items = ItemInBuilder()
none_of_items = ItemNotInBuilder()

key_matches = KeyMatchesBuilder()
any_key = AnyKeyBuilder()
any_of_keys = KeyInBuilder()
none_of_keys = KeyNotInBuilder()

index_matches = IndexMatchesBuilder()
any_index = AnyIndexBuilder()
any_of_indices = IndexInBuilder()
none_of_indices = IndexNotInBuilder()

if __name__ == "__main__":
    import doctest

    doctest.testmod()
