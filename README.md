# sans

[![pypi](https://img.shields.io/pypi/v/sans.svg) ![Licensed under the MIT License](https://img.shields.io/pypi/l/sans.svg)](https://pypi.org/project/sans/)
[![Downloads](https://static.pepy.tech/badge/sans)](https://pepy.tech/project/sans)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Zephyrkul/sans/master.svg)](https://results.pre-commit.ci/latest/github/Zephyrkul/sans/master)
[![Documentation Status](https://readthedocs.org/projects/sans/badge/?version=latest)](http://sans.readthedocs.org/en/latest/?badge=latest)

**S**ynchronous / **A**synchronous **N**ation**S**tates

A [fully typed](https://docs.python.org/3/library/typing.html>) extension for [HTTPX](https://www.python-httpx.org/) for the [NationStates API](https://www.nationstates.net/pages/api.html).

## Installing

```sh
python3 -m pip install -U sans
```

Development version:

```sh
python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans
```

## Examples

### Synchronous

```py
import sans
from xml.etree import ElementTree as ET

def main():
   sans.set_agent("Darcania")
   request = sans.Nation(
      "darcania",
      "fullname population flag census",
      mode="score",
      scale="65 66",
   )
   root = sans.get(request).xml
   sans.indent(root)
   print(ET.tostring(root, encoding="unicode"))

   with sans.stream("GET", sans.RegionsDump()) as response:
      for region in response.iter_xml():
         sans.indent(region)
         print(ET.tostring(region, encoding="unicode"))

if __name__ == "__main__":
   main()
```

### Asynchronous

```py
import asyncio
import sans
from xml.etree import ElementTree as ET

async def main():
   sans.set_agent("Darcania")
   async with sans.AsyncClient() as client:
      request = sans.Nation(
         "darcania",
         "fullname population flag census",
         mode="score",
         scale="65 66",
      )
      root = (await client.send(request)).xml
      sans.indent(root)
      print(ET.tostring(root, encoding="unicode"))

      async with client.stream("GET", sans.RegionsDump()) as response:
         async for region in response.aiter_xml():
            sans.indent(region)
            print(ET.tostring(region, encoding="unicode"))

if __name__ == "__main__":
   asyncio.run(main())
```

## Command Line

```xml
sans --nation darcania census --scale "65 66" --mode score --agent Darcania
<CENSUS>
   <SCALE id="65">
      <SCORE>4949.00</SCORE>
   </SCALE>
   <SCALE id="66">
      <SCORE>130.00</SCORE>
   </SCALE>
</CENSUS>

sans --nation testlandia fullname
<FULLNAME>The Hive Mind of Testlandia</FULLNAME>

sans --region "the north pacific" numnations lastupdate
<LASTUPDATE>1683650325</LASTUPDATE>
<NUMNATIONS>10503</NUMNATIONS>

sans --quit
No query provided. Exiting...
```

## Requirements

- [Python 3.7+](https://www.python.org/)
- [httpx](https://pypi.org/project/httpx/)
