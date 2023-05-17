from __future__ import annotations

import codecs
import zlib
from functools import reduce
from operator import itemgetter
from typing import TYPE_CHECKING, Iterable
from xml.etree.ElementTree import Element, XMLParser, XMLPullParser

if TYPE_CHECKING:
    from typing_extensions import Literal


def _reducer(final: bool):
    def inner(data: bytes, decoder: codecs.IncrementalDecoder) -> bytes:
        return decoder.decode(data, final)  # type: ignore

    return inner


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
        self._decoder_chain: list[codecs.IncrementalDecoder] = []
        if encoding:
            self._decoder_chain.append(
                codecs.getincrementaldecoder(encoding)("replace")
            )
        self._pull_parser = XMLPullParser(["start", "end"])
        self._path: list[Element] = []

    def decode(self, data: bytes) -> Iterable[Element]:
        data = reduce(_reducer(False), self._decoder_chain, data)
        self._pull_parser.feed(data)
        return map(itemgetter(1), self._read_events())

    def flush(self) -> Iterable[Element]:
        data = reduce(_reducer(True), self._decoder_chain, b"")
        self._pull_parser.feed(data)
        self._pull_parser.close()
        return map(itemgetter(1), self._read_events())

    def _read_events(self) -> Iterable[tuple[Literal["end"], Element]]:
        element: Element
        path = self._path
        for event, element in self._pull_parser.read_events():
            if event == "start":
                path.append(element)
            elif event == "end":
                path.pop()
                if len(path) == 1:
                    yield event, element
                    path[0].clear()


try:
    from lxml.etree import (
        XMLParser as LXMLParser,
        _Element as LElement,
    )
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
