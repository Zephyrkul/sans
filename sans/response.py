from __future__ import annotations

from email.message import Message
from itertools import chain
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator
from xml.etree.ElementTree import Element

import httpx

from .decoder import GZipDecoder, XMLChunker, XMLDecoder
from .errors import narrow

if TYPE_CHECKING:
    from typing_extensions import Self

    import xmltodict
    from lxml.etree import _Element
    from lxml.objectify import ObjectifiedElement

    from .decoder import LXMLDecoder, ObjectifyDecoder

    HAS_XMLTODICT: bool = True
    HAS_LXML: bool = True
else:
    try:
        import xmltodict

        HAS_XMLTODICT = True
    except ModuleNotFoundError:
        HAS_XMLTODICT = False

    try:
        from lxml.etree import _Element
        from lxml.objectify import ObjectifiedElement

        HAS_LXML = True
    except ModuleNotFoundError:
        HAS_LXML = False
    else:
        from .decoder import LXMLDecoder, ObjectifyDecoder

__all__ = ["Response"]


class Response(httpx.Response):
    @property
    def content_type(self) -> str:
        if not hasattr(self, "_content_type"):
            message = Message()
            content_type = self.headers.get("Content-Type")
            if content_type:
                message["Content-Type"] = self.headers.get("Content-Type")
            self._content_type = message.get_content_type()
        return self._content_type

    def iter_gzip(self) -> Iterator[bytes]:
        decoder = GZipDecoder()
        yield from map(decoder.decode, self.iter_bytes())
        yield decoder.flush()

    async def aiter_gzip(self) -> AsyncIterator[bytes]:
        decoder = GZipDecoder()
        async for chunk in self.aiter_bytes():
            yield decoder.decode(chunk)
        yield decoder.flush()

    if HAS_XMLTODICT:

        def json(self, **kwargs: Any) -> dict[str, Any]:
            if self.content_type.endswith("/xml"):
                return xmltodict.parse(self.content, encoding=self.encoding, **kwargs)
            return super().json(**kwargs)

    @property
    def xml(self) -> Element:
        if not hasattr(self, "_xml"):
            content = self.content
            decoder = XMLDecoder(self.encoding)
            decoder.decode(content)
            self._xml = decoder.flush()
        return self._xml

    def iter_xml(self) -> Iterator[Element]:
        decoder = XMLChunker(encoding=self.encoding)
        chunker = (
            self.iter_gzip()
            if self.content_type.endswith(("/x-gzip", "/gzip"))
            else self.iter_bytes()
        )
        yield from chain.from_iterable(map(decoder.decode, chunker))
        yield from decoder.flush()

    async def aiter_xml(self) -> AsyncIterator[Element]:
        decoder = XMLChunker(encoding=self.encoding)
        chunker = (
            self.aiter_gzip()
            if self.content_type.endswith(("/x-gzip", "/gzip"))
            else self.aiter_bytes()
        )
        async for chunk in chunker:
            for element in decoder.decode(chunk):
                yield element
        for element in decoder.flush():
            yield element

    if HAS_LXML:

        @property
        def lxml(self) -> _Element:
            if not hasattr(self, "_lxml"):
                content = self.content
                decoder = LXMLDecoder(self.encoding)
                decoder.decode(content)
                self._lxml = decoder.flush()
            return self._lxml

        @property
        def objectified(self) -> ObjectifiedElement:
            if not hasattr(self, "_objectified"):
                content = self.content
                decoder = ObjectifyDecoder(self.encoding)
                decoder.decode(content)
                self._objectified = decoder.flush()
            return self._objectified

    def raise_for_status(self) -> Self:  # type: ignore
        try:
            super().raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise narrow(exc).with_traceback(exc.__traceback__) from None
        return self
