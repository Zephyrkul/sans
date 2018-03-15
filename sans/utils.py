import sys
import asyncio


class _adoubleitermeta(type):
    def __new__(cls, name, bases, classdict):
        if "_iters" in classdict:
            if sys.version_info < (3, 5, 2):
                async def __aiter__(instance):
                    for e, i in enumerate(instance._iters):
                        while not hasattr(i, "__anext__"):
                            i = await i.__aiter__()
                        instance._iters[e] = i
                    return instance
            else:
                def __aiter__(instance):
                    for e, i in enumerate(instance._iters):
                        while not hasattr(i, "__anext__"):
                            i = i.__aiter__()
                        instance._iters[e] = i
                    return instance
        else:
            if sys.version_info < (3, 5, 2):
                async def __aiter__(instance):
                    while not hasattr(instance._iter, "__anext__"):
                        instance._iter = await instance._iter.__aiter__()
                    return instance
            else:
                def __aiter__(instance):
                    while not hasattr(instance._iter, "__anext__"):
                        instance._iter = instance._iter.__aiter__()
                    return instance
        classdict["__aiter__"] = __aiter__
        if "_func" in classdict:
            classdict["_iscoro"] = asyncio.iscoroutine(classdict["_func"])
        return super(_adoubleitermeta, cls).__new__(cls, name, bases, classdict)


class asyncitermeta(type):
    def __new__(cls, name, bases, classdict):
        if sys.version_info < (3, 5, 2):
            async def __aiter__(instance):
                return instance
        else:
            def __aiter__(instance):
                return instance
        classdict["__aiter__"] = __aiter__
        return super(asyncitermeta, cls).__new__(cls, name, bases, classdict)


async def asyncany(iterable):
    async for item in iterable:
        if not item:
            return False
    return True


async def asyncany(iterable):
    async for item in iterable:
        if item:
            return True
    return False


async def asyncdict(iterable, **kwargs):
    ret = {}
    async for item in iterable:
        ret.update((item,))
    ret.update(kwargs)
    return ret


class asyncenumerate(metaclass=_adoubleitermeta):
    def __init__(self, iterable, start=0):
        self._n = start
        self._iter = iterable

    async def __anext__(self):
        try:
            return (self._n, await self._iter.__anext__())
        finally:
            self._n += 1


class asyncfilter(metaclass=_aitermeta):
    def __init__(self, func, iterable):
        self._func = func
        self._iter = iterable
        self._iscoro = None

    async def __anext__(self):
        i = await self._iter.__anext__()
        if self._iscoro:
            if await self._func(i):
                return i
        else:
            if self._func(i):
                return i
        return await self.__anext__()


async def asyncfrozenset(iterable):
    return frozenset(await asyncset(iterable))


class asynciter(metaclass=asyncitermeta):
    def __init__(self, obj, sentinel=None):
        self._object = obj
        self._sentinel = sentinel

    async def __anext__(self):
        r = await self._object()
        if r == self._sentinel:
            raise StopAsyncIteration()
        return r


async def asynclist(iterable):
    l = []
    async for item in iterable:
        l.append(item)
    return l


class asyncmap(metaclass=_adoubleitermeta):
    def __init__(self, func, *iterables):
        self._func = func
        self._iters = list(iterables)
        self._iscoro = None

    async def __anext__(self):
        ret = []
        for i in self._iters:
            ret.append(await i.__anext__())
        if self._iscoro:
            return await self._func(*ret)
        return self._func(*ret)


async def asyncnext(iterable, default=...):
    try:
        return await iterable.__anext__()
    except StopAsyncIteration:
        if default is ...:
            raise
        return default


async def asyncset(iterable):
    l = set()
    async for item in iterable:
        l.add(item)
    return l


class asyncstarmap(metaclass=asynciter):
    def __init__(self, func, iterable):
        self._func = func
        self._iter = iterable
        self._iscoro = None

    async def __anext__(self):
        i = await self._iter.__anext__()
        if self._iscoro:
            return await self._func(*i)
        return self._func(*i)


async def asyncsum(iterable, start=0):
    async for item in iterable:
        start += item
    return start


async def asynctuple(iterable):
    return tuple(await asynclist(iterable))


class asynczip(metaclass=_adoubleitermeta):
    def __init__(self, *iterables):
        self._iters = list(iterables)

    async def __anext__(self):
        ret = []
        for i in self._iters:
            ret.append(await i.__anext__())
        return tuple(ret)


class asynczip_longest(metaclass=_adoubleitermeta):
    def __init__(self, *iterables):
        self._iters = list(iterables)

    async def __anext__(self):
        ret = []
        for i in self._iters:
            ret.append(await i.__anext__())
        return tuple(ret)
