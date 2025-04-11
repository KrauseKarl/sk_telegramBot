from enum import Enum


class Navigation(str, Enum):
    next = "NXT"
    prev = "PRV"
    last = "LST"
    first = "FRT"
