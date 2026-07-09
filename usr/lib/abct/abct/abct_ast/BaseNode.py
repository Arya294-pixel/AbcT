from enum import Enum as _Enum, auto
from dataclasses import dataclass

def frozendataclass(cls):
    return dataclass(frozen=True, slots=True)(cls)

class BaseEnum(_Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

@frozendataclass
class Node: pass

@frozendataclass
class Type(Node): pass
