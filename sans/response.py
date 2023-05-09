from __future__ import annotations

import cgi
from collections import deque
from itertools import chain
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    pass

import httpx

from .decoder import XMLChunker, XMLDecoder
from .errors import narrow

try:
    import xmltodict

    HAS_XMLTODICT = True
except ImportError:
    HAS_XMLTODICT = False  # type: ignore

try:
    from lxml.etree import _Element  # type: ignore

    HAS_LXML = True
except ImportError:
    HAS_LXML = False  # type: ignore
else:
    from .decoder import LXMLChunker, LXMLDecoder


__all__ = ["Response"]


class Response(httpx.Response):
    def _is_xml(self) -> bool:
        raw_content_type = self.headers.get("Content-Type")
        if not raw_content_type:
            return False
        content_type, _ = cgi.parse_header(raw_content_type)
        return content_type == "text/xml"

    if HAS_XMLTODICT:

        def json(self) -> dict[str, Any]:
            if self._is_xml():
                return xmltodict.parse(self.text)
            return super().json()

    @property
    def xml(self) -> Element:
        if not hasattr(self, "_xml"):
            content = self.content
            decoder = XMLDecoder(self.encoding or "utf-8")
            tail = deque(chain(decoder.feed(content), decoder.flush()), maxlen=1)
            self._xml = next(iter(tail))
        return self._xml

    def iter_xml(self) -> Iterator[Element]:
        decoder = XMLChunker(self.encoding or "utf-8")
        for chunk in self.iter_bytes():
            yield from decoder.feed(chunk)
        yield from decoder.flush()

    async def aiter_xml(self) -> AsyncIterator[Element]:
        decoder = XMLChunker(self.encoding or "utf-8")
        async for chunk in self.aiter_bytes():
            for element in decoder.feed(chunk):
                yield element
        for element in decoder.flush():
            yield element

    if HAS_LXML:

        @property
        def lxml(self) -> _Element:
            if not hasattr(self, "_lxml"):
                content = self.content
                decoder = LXMLDecoder(self.encoding or "utf-8")
                tail = deque(chain(decoder.feed(content), decoder.flush()), maxlen=1)
                self._lxml = next(iter(tail))
            return self._lxml

        def iter_lxml(self) -> Iterator[_Element]:
            decoder = LXMLChunker(self.encoding or "utf-8")
            for chunk in self.iter_bytes():
                yield from decoder.feed(chunk)
            yield from decoder.flush()

        async def aiter_lxml(self) -> AsyncIterator[_Element]:
            decoder = LXMLChunker(self.encoding or "utf-8")
            async for chunk in self.aiter_bytes():
                for element in decoder.feed(chunk):
                    yield element
            for element in decoder.flush():
                yield element

    def raise_for_status(self) -> None:
        try:
            return super().raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise narrow(exc) from None
