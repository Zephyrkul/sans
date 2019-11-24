sans
====

|pypi| |Code style: black| |Build Status| |Documentation Status|

Synchronous / Asynchronous NationStates (Python wrapper for the
NationStates API)

Note
~~~~
While this library can be run in a single-threaded, synchronous environment,
it is highly recommended to use Dolph's pynationstates
(`GitHub <https://github.com/DolphDev/pynationstates>`_
| `PyPI <https://pypi.org/project/nationstates/>`_) for simpler scripts.

Installing
----------

::

   python3 -m pip install -U sans

Development version:

::

   python3 -m pip install -U https://github.com/zephyrkul/sans/archive/master.zip#egg=sans

Examples
--------

Asynchronous
~~~~~~~~~~~~

.. code:: py

   import asyncio
   import sans
   from sans.api import Api, Dumps
   from sans.utils import pretty_string

   async def main():
       Api.agent = "Darcania"
       request = Api(
           "fullname population flag census",
           nation="darcania",
           mode="score",
           scale="65 66",
       )
       root = await request
       pretty = pretty_string(root)
       print(pretty)

       request = Dumps.REGIONS
       async for region in request:
           pretty = pretty_string(region)
           print(pretty)


   asyncio.run(main())  # Python 3.7+ only

Synchronous
~~~~~~~~~~~

.. code:: py

   import sans
   from sans.api import Api, Dumps

   def main():
       sans.run_in_thread()
       Api.agent = "Darcania"
       request = Api(
           "fullname population flag census",
           nation="darcania",
           mode="score",
           scale="65 66",
       )
       root = request.threadsafe()
       pretty = pretty_string(root)
       print(pretty)

       request = Dumps.REGIONS
       for region in request.threadsafe:
           pretty = pretty_string(region)
           print(pretty)


   main()

Command Line
------------

::

   python3 -m sans --nation darcania census --scale "65 66" --mode score --agent Darcania
   <NATION>...</NATION>
   sans --nation testlandia fullname
   <NATION>...</NATION>
   sans --region "the north pacific" numnations lastupdate
   <REGION>...</REGION>
   sans --quit
   Exiting...

Requirements
------------

-  Python 3.6+
-  aiohttp
-  lxml

.. |pypi| image:: https://img.shields.io/pypi/v/sans.svg
   :target: https://pypi.python.org/pypi/sans
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black
.. |Build Status| image:: https://github.com/zephyrkul/sans/workflows/build/badge.svg
   :target: https://github.com/zephyrkul/sans/actions?workflow=build
.. |Documentation Status| image:: https://readthedocs.org/projects/sans/badge/?version=latest
   :target: http://sans.readthedocs.org/en/latest/?badge=latest
