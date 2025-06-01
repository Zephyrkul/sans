from __future__ import annotations

import codecs
import zlib
from typing import Iterable, TypeVar
from xml.etree.ElementTree import Element, XMLParser, XMLPullParser

_T = TypeVar("_T")


class NullIncrementalDecoder:
    @staticmethod
    def decode(input: _T, final: bool = False) -> _T:
        return input


class GZipDecoder:
    def __init__(self) -> None:
        self._decompressobj = zlib.decompressobj(zlib.MAX_WBITS | 16)

    def decode(self, data: bytes) -> bytes:
        return self._decompressobj.decompress(data)

    def flush(self) -> bytes:
        return self._decompressobj.flush()


class XMLDecoder:
    def __init__(self, encoding: str | None = None) -> None:
        self._parser = XMLParser(encoding=encoding)

    def decode(self, data: bytes) -> None:
        self._parser.feed(data)

    def flush(self) -> Element:
        return self._parser.close()


class XMLChunker:
    def __init__(self, *, encoding: str | None = None) -> None:
        self._decoder = (
            codecs.getincrementaldecoder(encoding)("replace")
            if encoding
            else NullIncrementalDecoder
        )
        self._pull_parser = XMLPullParser(["start", "end"])
        self._path: list[Element] = []

    def decode(self, data: bytes) -> Iterable[Element]:
        self._pull_parser.feed(self._decoder.decode(data, False))
        return self._read_events()

    def flush(self) -> Iterable[Element]:
        self._pull_parser.feed(self._decoder.decode(b"", True))
        self._pull_parser.close()
        return self._read_events()

    def _read_events(self) -> Iterable[Element]:
        element: Element
        path = self._path
        for event, element in self._pull_parser.read_events():  # type: ignore
            if event == "start":
                path.append(element)
            elif event == "end":
                path.pop()
                if len(path) == 1:
                    yield element
                    path[0].clear()


try:
    from lxml.etree import (
        XMLParser as LXMLParser,
        _Element as LElement,
    )
    from lxml.objectify import ObjectifiedElement, ObjectifyElementClassLookup
except ImportError:
    pass
else:

    class LXMLDecoder:
        def __init__(self, encoding: str | None = None) -> None:
            self._parser = LXMLParser(encoding=encoding)

        def decode(self, data: bytes) -> None:
            self._parser.feed(data)

        def flush(self) -> LElement:
            return self._parser.close()

    class ObjectifyDecoder:
        def __init__(self, encoding: str | None = None) -> None:
            self._parser = parser = LXMLParser(
                encoding=encoding, remove_blank_text=True
            )
            parser.set_element_class_lookup(ObjectifyElementClassLookup())

        def decode(self, data: bytes) -> None:
            self._parser.feed(data)

        def flush(self) -> ObjectifiedElement:
            return self._parser.close()  # type: ignore
