from dataclasses import dataclass
from enum import Enum


class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


@dataclass(frozen=True)
class Item:
    id: int
    name: str
    rarity: Rarity
    icon: str


@dataclass(frozen=True)
class Student:
    id: int
    name: str
    icon: str
    hasBondGear: bool
    StarGrade: int


@dataclass(frozen=True)
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str


# ? Will use it on future idk
# @dataclass(frozen=True)
# class ReleaseStatus:
#     jp: bool = False
#     en: bool = False
#     cn: bool = False
