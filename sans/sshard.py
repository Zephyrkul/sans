from enum import Enum, unique

__all__ = []

@unique
class SShard(str, Enum):
    wa = "UNSTATUS"

    @classmethod
    def sshard(cls, s):
        try:
            if s.tag == "CENSUSSCORE":
                return "censusscore-" + s.attrib["id"]
        except AttributeError:
            if not isinstance(s, str):
                return s
        else:
            s = s.tag
        try:
            return cls(s.upper()).name
        except ValueError:
            return s.lower()