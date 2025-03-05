from __future__ import annotations

from datetime import date as _date
from itertools import starmap
from typing import TYPE_CHECKING, Callable, Dict, Iterable, Mapping, NewType

import httpx

if TYPE_CHECKING:
    from typing_extensions import Literal, TypeAlias, TypeVar

    _T = TypeVar("_T")

    _Shard = NewType("_Shard", Dict[str, str])
    _QueryValueTypes: TypeAlias = "str | int | float | bool"

API_URL = httpx.URL("https://www.nationstates.net/cgi-bin/api.cgi")

__all__ = [
    "API_URL",
    "Nation",
    "Region",
    "World",
    "WA",
    "Command",
    "Shard",
    "View",
    "Range",
    "NationsDump",
    "RegionsDump",
    "CardsDump",
    "Telegram",
]


class _encoder:
    def nation(self, nation: _QueryValueTypes) -> str:
        return str(nation).replace(" ", "_")

    region = nation

    def to(self, to: _T) -> _T | str:
        if isinstance(to, str):
            return self.nation(to)
        return to

    def q(self, q: _QueryValueTypes) -> str:
        return str(q)

    def __getattr__(self, _) -> Callable[[_T], _T]:
        return lambda x: x

    def __call__(
        self, key: str, value: _QueryValueTypes
    ) -> tuple[str, _QueryValueTypes]:
        return key, getattr(self, key)(value)


def Nation(
    nation: str, *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, nation=nation, **parameters)


def Region(
    region: str, *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, region=region, **parameters)


def World(*shards: str | _Shard, **parameters: _QueryValueTypes) -> httpx.URL:
    encoder = _encoder()
    q: list[_QueryValueTypes | None] = [parameters.pop("q", None)]
    query: dict[str, _QueryValueTypes] = {}
    for shard in shards:
        if isinstance(shard, Mapping):
            shard = dict(shard)
            q.append(shard.pop("q", None))
            query.update(starmap(encoder, shard.items()))
        else:
            q.append(str(shard))
    q_str = " ".join(map(encoder.q, filter(None, q)))
    if q_str:
        query["q"] = q_str
    query.update(parameters)
    return API_URL.copy_with(params=query)


def WA(
    wa: Literal[1, "1", 2, "2"], *shards: str | _Shard, **parameters: _QueryValueTypes
) -> httpx.URL:
    return World(*shards, wa=str(wa), **parameters)


def Command(nation: str, c: str, **parameters: _QueryValueTypes) -> httpx.URL:
    return World(nation=nation, c=c, **parameters)


def Telegram(client: str, tgid: str, key: str, to: str) -> httpx.URL:
    return World(a="sendtg", client=client, tgid=tgid, key=key, to=to)


def Shard(q: str, **parameters: _QueryValueTypes) -> _Shard:
    parameters["q"] = q
    return parameters  # type: ignore


def View(*, nations: Iterable[str] = (), regions: Iterable[str] = ()) -> _Shard:
    encoder = _encoder()
    nations = ",".join(
        map(encoder.nation, (nations,) if isinstance(nations, str) else nations)
    )
    regions = ",".join(
        map(encoder.region, (regions,) if isinstance(regions, str) else regions)
    )
    view = " ".join(filter(len, (nations, regions)))
    if view:
        return {"view": view}  # type: ignore
    return {}  # type: ignore


def Range(__from: _QueryValueTypes, __to: _QueryValueTypes) -> _Shard:
    return {"from": __from, "to": __to}  # type: ignore


# https://www.nationstates.net/archive/nations/2018-09-30-nations-xml.gz
def NationsDump(date: _date | None = None) -> httpx.URL:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-nations-xml.gz")
    else:
        path = "/pages/nations.xml.gz"
    return API_URL.join(path)


# https://www.nationstates.net/archive/nations/2018-09-30-regions-xml.gz
def RegionsDump(date: _date | None = None) -> httpx.URL:
    if date:
        path = date.strftime("/archive/nations/%Y-%m-%d-regions-xml.gz")
    else:
        path = "/pages/regions.xml.gz"
    return API_URL.join(path)


def CardsDump(season: Literal[1, "1", 2, "2", 3, "3", 4, "4"]) -> httpx.URL:
    return API_URL.join(f"/pages/cardlist_S{season}.xml.gz")
