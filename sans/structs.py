from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


__all__ = []


def sanitize(value):
    if not value:
        return None
    if not isinstance(value, str):
        try:
            value = " ".join(map(str, value))
        except TypeError:
            value = str(value)
    return value.lower()


class qdict(dict):

    def __init__(self, setkey: str, query: str=None, **kwargs):
        super(qdict, self).__init__(self)
        self._skey = setkey.lower()
        self._svalue = qset()
        super(qdict, self).__setitem__(self._skey, self._svalue)
        self.update(parse_qs(urlparse(query).query), **kwargs)

    def update(self, other={}, **kwargs):
        other = other.copy()
        other.update(kwargs)
        l = sanitize(other.pop(self._skey))
        if l:
            self().add(*l.split())
        for key, value in other.items():
            if value:
                self[key] = value

    def __call__(self):
        return self._svalue

    def __setitem__(self, key, value):
        if not key or not value:
            raise ValueError("Falsey item: {!r}: {!r}.".format(key, value))
        key = str(key).lower()
        if key == self._skey:
            raise ValueError(key)
        value = sanitize(value)
        if key == self._skey:
            return super(qdict, self).__setitem__(key, self._svalue)
        return super(qdict, self).__setitem__(key, value)

    def __delitem__(self, key):
        key = str(key).lower()
        if key == self._skey:
            raise KeyError(key)
        return super(qdict, self).__delitem__(key)

    def __str__(self):
        d = dict(self)
        if self():
            d[self._skey] = str(self())
        else:
            del d[self._skey]
        return urlencode(d)

    @property
    def query(self):
        return str(self)

    @query.setter
    def query(self, query):
        self.clear()
        self().clear()
        self[self._skey] = self()
        return self.update(parse_qs(urlparse(query).query))


class qset:
    def __init__(self, *values):
        self._set = set(map(sanitize, values))

    def __str__(self):
        return " ".join(self)

    def __iter__(self):
        return iter(self._set)

    def __eq__(self, other):
        return self._set == set(other)

    def add(self, *values):
        return self._set.update(map(sanitize, values))

    def discard(self, *values):
        return self._set.difference_update(map(sanitize, values))

    def clear(self):
        return self._set.clear()
