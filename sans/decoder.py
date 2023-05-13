from __future__ import annotations

import codecs
import zlib
from operator import itemgetter
from typing import TYPE_CHECKING, Iterable
from xml.etree.ElementTree import Element, XMLParser, XMLPullParser

if TYPE_CHECKING:
    from typing_extensions import Literal


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
        self._root: Element | None = None

    def decode(self, data: bytes) -> Iterable[Element]:
        for chain in self._decoder_chain:
            data = chain.decode(data, False)  # type: ignore
        self._pull_parser.feed(data)
        return map(itemgetter(1), self._read_events())

    def flush(self, data: bytes = b"") -> Iterable[Element]:
        for chain in self._decoder_chain:
            data = chain.decode(data, True)  # type: ignore
        self._pull_parser.feed(data)
        self._pull_parser.close()
        return map(itemgetter(1), self._read_events())

    def _read_events(self) -> Iterable[tuple[Literal["end"], Element]]:
        depth = 0
        element: Element
        for event, element in self._pull_parser.read_events():
            if not self._root:
                self._root = element
            if event == "start":
                depth += 1
            elif event == "end":
                depth -= 1
                if depth == 1:
                    yield event, element
                    self._root.clear()


try:
    from lxml.etree import (
        XMLParser as LXMLParser,
        XMLPullParser as LXMLPullParser,
        _Element as LElement,  # type: ignore
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

    class LXMLChunker:
        def __init__(self, *, encoding: str | None = None) -> None:
            self._decoder_chain: list[codecs.IncrementalDecoder] = []
            if encoding:
                self._decoder_chain.append(
                    codecs.getincrementaldecoder(encoding)("replace")
                )
            self._pull_parser = LXMLPullParser(["start", "end"])

        def decode(self, data: bytes) -> Iterable[LElement]:
            for chain in self._decoder_chain:
                data = chain.decode(data, False)  # type: ignore
            self._pull_parser.feed(data)
            return map(itemgetter(1), self._read_events())

        def flush(self, data: bytes = b"") -> Iterable[LElement]:
            for chain in self._decoder_chain:
                data = chain.decode(data, True)  # type: ignore
            self._pull_parser.feed(data)
            self._pull_parser.close()
            return map(itemgetter(1), self._read_events())

        def _read_events(self) -> Iterable[tuple[Literal["end"], LElement]]:
            depth = 0
            element: LElement
            for event, element in self._pull_parser.read_events():  # type: ignore
                if not self._root:
                    self._root = element
                if event == "start":
                    depth += 1
                elif event == "end":
                    depth -= 1
                    if depth == 1:
                        yield event, element
                        self._root.clear()
