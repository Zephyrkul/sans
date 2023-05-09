from __future__ import annotations

import codecs
from operator import attrgetter, itemgetter
from typing import TYPE_CHECKING, Iterable
from xml.etree.ElementTree import Element, XMLPullParser

if TYPE_CHECKING:
    from typing_extensions import Literal


class XMLDecoder:
    _events = ["end"]
    _read_events = property(attrgetter("_pull_parser.read_events"))

    def __init__(self, encoding: str = "utf-8") -> None:
        self._decoder = codecs.getincrementaldecoder(encoding)("xmlcharrefreplace")
        self._pull_parser = XMLPullParser(self._events)

    def feed(self, data: bytes) -> Iterable[Element]:
        self._pull_parser.feed(self._decoder.decode(data, False))
        return map(itemgetter(1), self._read_events())

    def flush(self) -> Iterable[Element]:
        self._pull_parser.feed(self._decoder.decode(b"", True))
        self._pull_parser.close()
        return map(itemgetter(1), self._read_events())


class XMLChunker(XMLDecoder):
    _events = ["start", "end"]
    _root: Element | None = None

    def _read_events(self) -> Iterable[tuple[Literal["end"], Element]]:
        depth = 0
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
    from lxml.etree import XMLPullParser as LXMLPullParser, _Element as LElement
except ImportError:
    pass
else:

    class LXMLDecoder:
        _events = ["end"]
        _read_events = property(attrgetter("_pull_parser.read_events"))

        def __init__(self, encoding: str = "utf-8") -> None:
            self._decoder = codecs.getincrementaldecoder(encoding)("xmlcharrefreplace")
            # the typehint below is close enough due to missing stubs
            self._pull_parser: XMLPullParser = LXMLPullParser(self._events)

        def feed(self, data: bytes) -> Iterable[LElement]:
            self._pull_parser.feed(self._decoder.decode(data, False))
            return map(itemgetter(1), self._read_events())

        def flush(self) -> Iterable[LElement]:
            self._pull_parser.feed(self._decoder.decode(b"", True))
            self._pull_parser.close()
            return map(itemgetter(1), self._read_events())

    class LXMLChunker(LXMLDecoder):
        _events = ["start", "end"]

        def _read_events(self) -> Iterable[tuple[Literal["end"], LElement]]:
            element: LElement
            depth = 0
            for event, element in self._pull_parser.read_events():
                if event == "start":
                    depth += 1
                else:
                    assert event == "end"
                    depth -= 1
                    if depth == 1:
                        yield event, element
                        element.clear(keep_tail=True)  # type: ignore
                        while element.getprevious() is not None:
                            del element.getparent()[0]  # type: ignore
