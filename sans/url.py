from __future__ import annotations

from datetime import date as _date
from typing import TYPE_CHECKING, Mapping

import httpx

if TYPE_CHECKING:
    from typing_extensions import Literal
API_URL = httpx.URL("https://www.nationstates.net/cgi-bin/api.cgi")

__all__ = [
    "API_URL",
    "Nation",
    "Region",
    "World",
    "WA",
    "Shard",
    "NationsDump",
    "RegionsDump",
    "CardsDump",
]


def Nation(nation: str, *shards: str, **parameters: str) -> httpx.URL:
    return World(*shards, nation=nation, **parameters)


def Region(region: str, *shards: str, **parameters: str) -> httpx.URL:
    return World(*shards, region=region, **parameters)


def World(*shards: str | Mapping[str, str], **parameters: str) -> httpx.URL:
    q: list[str | None] = [parameters.pop("q", None)]
    query: dict[str, str] = {}
    for shard in shards:
        try:
            shard = dict(shard)  # type: ignore
        except (TypeError, ValueError):
            q.append(str(shard))
        else:
            q.append(shard.pop("q", None))  # type: ignore
            query.update(shard)  # type: ignore
    query.update(parameters, q=" ".join(map(str, filter(None, q))))
    if query.get("a", "").lower() == "sendtg":
        raise RuntimeError("sans does not currently support the telegram API.")
    return API_URL.copy_with(params=query)


def WA(wa: Literal[1, "1", 2, "2"], *shards: str, **parameters: str) -> httpx.URL:
    return World(*shards, wa=str(wa), **parameters)


def Shard(q: str, **parameters: str) -> dict[str, str]:
    parameters["q"] = q
    return parameters


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


def CardsDump(season: Literal[1, "1", 2, "2", 3, "3"]) -> httpx.URL:
    return API_URL.join(f"/pages/cardlist_S{season}.xml.gz")
