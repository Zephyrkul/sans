from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING, Dict, Mapping, NewType

import httpx

if TYPE_CHECKING:
    from typing_extensions import Literal

    _Shard = NewType("_Shard", Dict[str, str])

API_URL = httpx.URL("https://www.nationstates.net/cgi-bin/api.cgi")

__all__ = [
    "API_URL",
    "Nation",
    "Region",
    "World",
    "WA",
    "Command",
    "Shard",
    "NationsDump",
    "RegionsDump",
    "CardsDump",
    "Telegram",
]


def Nation(nation: str, *shards: str | _Shard, **parameters: str) -> httpx.URL:
    return World(*shards, nation=nation, **parameters)


def Region(region: str, *shards: str, **parameters: str) -> httpx.URL:
    return World(*shards, region=region, **parameters)


def World(*shards: str | _Shard, **parameters: str) -> httpx.URL:
    q: list[str | None] = [parameters.pop("q", None)]
    query: dict[str, str] = {}
    for shard in shards:
        if isinstance(shard, Mapping):
            shard = dict(shard)
            q.append(shard.pop("q", None))
            query.update(shard)
        else:
            q.append(str(shard))
    q_str = " ".join(map(str, filter(None, q)))
    if q_str:
        query["q"] = q_str
    query.update(parameters)
    return API_URL.copy_with(params=query)


def WA(
    wa: Literal[1, "1", 2, "2"], *shards: str | _Shard, **parameters: str
) -> httpx.URL:
    return World(*shards, wa=str(wa), **parameters)


def Command(nation: str, c: str, **parameters: str) -> httpx.URL:
    return World(nation=nation, c=c, **parameters)


def Telegram(client: str, tgid: str, key: str, to: str) -> httpx.URL:
    return World(a="sendtg", client=client, tgid=tgid, key=key, to=to)


def Shard(q: str, **parameters: str) -> _Shard:
    parameters["q"] = q
    return parameters  # type: ignore


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
