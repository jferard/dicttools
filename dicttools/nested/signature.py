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
from typing import (Callable, Any, Tuple, Sequence, Generic, TypeVar, Optional,
                    Union)
from dicttools.nested._occurrences import (Occurrences, once_instance,
                                           occurrences)


class Glob(ABC):
    """
    As in shell, `Glob` represents a chunk of a signature that can accept
    multiple values.
    """

    def try_key(self, k: Any) -> Optional["Glob"]:
        """
        Try to consume the key `j` and return the `Glob` after the key was
        accepted, or None.

        :param k: the key to test
        :return: a new instance of `Glob`
        :raise: KeyError if the key was not accepted
        """
        raise KeyError

    def try_index(self, j: int) -> Optional["Glob"]:
        """
        Try to consume the index `i` and return the `Glob` after the index was
        accepted.

        :param j: the index to test
        :return: a new instance of `Glob`
        :raise: IndexError if the key was not accepted
        """
        raise IndexError

    def can_skip(self) -> bool:
        """
        :return: True if this `Glob` can be skipped.
        """
        return False

    @abstractmethod
    def __repr__(self):
        pass


T = TypeVar('T', bound=Glob)


class GlobBuilder(ABC, Generic[T]):
    @abstractmethod
    def __getitem__(self, item: Union[slice, int]) -> T:
        pass


Chunk = Union[Any, Glob]


#######
# all #
#######
class AnyItem(Glob):
    def __init__(self, occurrences: Occurrences = once_instance):
        self._occurrences = occurrences

    def try_key(self, k: Any) -> Optional[Glob]:
        o = self._occurrences.next()
        if o is None:
            return None
        else:
            return AnyItem(o)

    def try_index(self, j: int) -> Optional[Glob]:
        o = self._occurrences.next()
        if o is None:
            return None
        else:
            return AnyItem(o)

    def can_skip(self) -> bool:
        return self._occurrences.can_skip()

    def __repr__(self):
        return f"any_item{self._occurrences}"


class any_item(GlobBuilder[AnyItem]):
    """
    >>> g = any_item[:2]
    >>> g.try_key(1)
    any_item[1:1]
    >>> g.try_key(1).try_key(1) is None
    True
   """

    def __class_getitem__(cls, item: Union[range, int]) -> AnyItem:
        """
        :param item: int or slice
        :return:
        """
        return AnyItem(occurrences(item))


class ItemIn(Glob):
    def __init__(self, vs: Union[Sequence[Any], Sequence[int]],
                 occurrences: Occurrences = once_instance):
        self._vs = vs
        self._occurrences = occurrences

    def try_key(self, k: Any) -> Optional[Glob]:
        if k in self._vs:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return KeyIn(self._vs, o)
        else:
            raise KeyError()

    def try_index(self, j) -> Optional[Glob]:
        if j in self._vs:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemIn(self._vs, o)
        else:
            raise IndexError()

    def __getitem__(self, item: Union[range, int]) -> Glob:
        return ItemIn(self._vs, occurrences(item))

    def __repr__(self):
        vs = ', '.join(str(v) for v in self._vs)
        return f"glob.item_in({vs})"


class ItemNotIn(Glob):
    def __init__(self, vs, occurrences=once_instance):
        self._vs = vs
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        if k in self._vs:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemNotIn(self._vs, o)
        else:
            raise KeyError()

    def try_index(self, j) -> Glob:
        if j in self._vs:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemNotIn(self._vs, o)
        else:
            raise IndexError()

    def __getitem__(self, item):
        return ItemNotIn(self._vs, occurrences(item))

    def __repr__(self):
        vs = ', '.join(str(v) for v in self._vs)
        return f"glob.item_not_in({vs})"


class ItemMatching(Glob):
    def __init__(self, func: Callable[[object], bool],
                 occurrences=once_instance):
        self._func = func
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        if self._func(k):
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemMatching(self._func, o)
        else:
            raise KeyError()

    def try_index(self, j) -> Glob:
        if self._func(j):
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemMatching(self._func, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return ItemMatching(self._func, occurrences(item))

    def __repr__(self):
        return f"glob.item_matching({self._func})"


########
# keys #
########
class AnyKey(Glob):
    def __init__(self, occurrences=once_instance):
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        o = self._occurrences.next()
        if o is None:
            return None
        else:
            return AnyKey(o)

    def can_skip(self) -> bool:
        return self._occurrences.can_skip()

    def __getitem__(self, item):
        """
        :param item: int or slice
        :return:
        """
        return AnyKey(occurrences(item))

    def __repr__(self):
        return f"any_key{self._occurrences}"


class KeyIn(Glob):
    def __init__(self, ks, occurrences=once_instance):
        self._ks = ks
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        if k in self._ks:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return KeyIn(self._ks, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return KeyIn(self._ks, occurrences(item))

    def __repr__(self):
        ks = ', '.join(str(k) for k in self._ks)
        return f"glob.key_in({ks})"


class KeyNotIn(Glob):
    def __init__(self, ks, occurrences=once_instance):
        self._ks = ks
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        if k in self._ks:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return KeyNotIn(self._ks, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return KeyNotIn(self._ks, occurrences(item))

    def __repr__(self):
        ks = ', '.join(str(k) for k in self._ks)
        return f"glob.key_not_in({ks})"


class KeyMatching(Glob):
    def __init__(self, func: Callable[[object], bool],
                 occurrences=once_instance):
        self._func = func
        self._occurrences = occurrences

    def try_key(self, k) -> Optional[Glob]:
        if self._func(k):
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return ItemMatching(self._func, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return ItemMatching(self._func, occurrences(item))

    def __repr__(self):
        return f"glob.key_matching({self._func})"


###########
# indices #
###########
class AnyIndex(Glob):
    def __init__(self, occurrences=once_instance):
        self._occurrences = occurrences

    def try_index(self, k) -> Optional[Glob]:
        o = self._occurrences.next()
        if o is None:
            return None
        else:
            return AnyIndex(o)

    def can_skip(self) -> bool:
        return self._occurrences.can_skip()

    def __getitem__(self, item):
        """
        :param item: int or slice
        :return:
        """
        return AnyIndex(occurrences(item))

    def __repr__(self):
        return f"any_index{self._occurrences}"


class IndexIn(Glob):
    def __init__(self, js, occurrences=once_instance):
        self._js = js
        self._occurrences = occurrences

    def try_index(self, j) -> Glob:
        if j in self._js:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return IndexIn(self._js, o)
        else:
            raise IndexError()

    def __getitem__(self, item):
        return IndexIn(self._js, occurrences(item))

    def __repr__(self):
        js = ', '.join(str(j) for j in self._js)
        return f"glob.index_in({js})"


class IndexNotIn(Glob):
    def __init__(self, js, occurrences=once_instance):
        self._js = js
        self._occurrences = occurrences

    def try_index(self, j) -> Glob:
        if j in self._js:
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return IndexNotIn(self._js, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return KeyNotIn(self._js, occurrences(item))

    def __repr__(self):
        ks = ', '.join(str(k) for k in self._js)
        return f"glob.index_not_in({ks})"


class IndexMatching(Glob):
    def __init__(self, func: Callable[[object], bool],
                 occurrences=once_instance):
        self._func = func
        self._occurrences = occurrences

    def try_index(self, j) -> Glob:
        if self._func(j):
            o = self._occurrences.next()
            if o is None:
                return None
            else:
                return IndexMatching(self._func, o)
        else:
            raise KeyError()

    def __getitem__(self, item):
        return IndexMatching(self._func, occurrences(item))

    def __repr__(self):
        return f"glob.index_matching({self._func})"


###########
# builder #
###########
class GlobBuilder0:
    def any_item(self):
        return AnyItem()

    def item_in(self, *keys):
        return ItemIn(keys)

    def item_not_in(self, *keys):
        return ItemNotIn(*keys)

    def item_matching(self, func):
        return ItemMatching(func)

    def any_key(self):
        return AnyKey()

    def key_in(self, *keys):
        return KeyIn(keys)

    def key_not_in(self, *keys):
        return KeyNotIn(*keys)

    def key_matching(self, func):
        return KeyMatching(func)

    def any_index(self):
        return AnyIndex()

    def index_in(self, *indices):
        return IndexIn(indices)

    def index_not_in(self, *indices):
        return IndexNotIn(*indices)

    def index_matching(self, func):
        return IndexMatching(func)


class Signature(Glob):
    """
    >>> Signature(any_key[:]).try_key("a")
    Signature(any_key[:])
    >>> Signature("b").try_key("b")
    Signature()
    >>> Signature("b").try_key("c")
    Traceback (most recent call last):
    ...
    KeyError: 'b vs c'
    """

    def __init__(self, *chunks: Chunk,
                 occurrences: Occurrences = once_instance):
        self._chunks = chunks
        self._occurrences = occurrences

    def try_key(self, k: Any) -> Optional["Signature"]:
        if not self._chunks:
            return None

        c0, *cs = self._chunks
        if c0 == k:
            return Signature(*cs)
        else:
            try:
                return self._try_key_glob(c0, cs, k)
            except AttributeError:
                raise KeyError(f"{c0} vs {k}")

    def _try_key_glob(self, c0: Chunk, cs: Tuple[Chunk], k: Any
                      ) -> Optional["Signature"]:
        try:
            c0 = c0.try_key(k)
        except KeyError:
            if c0.can_skip():
                return Signature(*cs).try_key(k)
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
        return f"Signature({chunks}){self._occurrences}"


def signature(*chunks):
    return Signature(chunks)


glob = GlobBuilder0()
# any_item = glob.any_item()
any_key = glob.any_key()
any_index = glob.any_index()
any_of_items = glob.item_in
any_of_keys = glob.key_in
any_of_indices = glob.index_in

if __name__ == "__main__":
    import doctest

    doctest.testmod()
