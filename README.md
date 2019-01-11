# sans

[![pypi](https://img.shields.io/pypi/v/sans.svg)](https://pypi.python.org/pypi/sans)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Build Status](https://travis-ci.com/zephyrkul/sans.svg?branch=master)](https://travis-ci.com/zephyrkul/sans)

Synchronous / Asynchronous NationStates (Python wrapper for the NationStates API)

## Installing

```
python3 -m pip install -U sans
```

Development version:
```
python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans
```

## Examples

### Asynchronous
```py
import asyncio
import sans
from lxml import etree

async def main():
    request = sans.Api(
        "fullname population flag census",
        nation="darcania",
        mode="score",
        scale="65 66",
    )
    root = await request
    pretty = etree.tostring(root, encoding=str, pretty_print=True)
    print(pretty)


asyncio.run(main())  # Python 3.7+ only
```

### Synchronous
```py
import sans
from lxml import etree

def main():
    sans.run_in_thread()
    request = sans.Api(
        "fullname population flag census",
        nation="darcania",
        mode="score",
        scale="65 66",
    )
    root = request.threadsafe()
    pretty = etree.tostring(root, encoding=str, pretty_print=True)
    print(pretty)


main()
```

## Command Line
```
python3 -m sans --nation darcania
>>> --nation testlandia
>>> exit
```

## Requirements
- Python 3.6+
- aiohttp
- lxml
