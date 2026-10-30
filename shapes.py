from dataclasses import dataclass
from enum import Enum


class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


class Category(Enum):
    CHARACTER_EXP_GROWTH = "CharacterExpGrowth"  # Activity Report
    COIN = "Coin"
    COLLECTIBLE = "Collectible"
    CONSUMABLE = "Consumable"
    FAVOR = "Favor"  # Gift
    MATERIAL = "Material"
    SECRET_STONE = "SecretStone"  # Eleph


class SubCategory(Enum):
    ARTIFACT = "Artifact"
    BOOK_ITEM = "BookItem"  # Tech Notes
    CD_ITEM = "CDItem"  # Tactical Training Blu-ray


@dataclass(frozen=True)
class Item:
    id: int
    category: Category
    rarity: Rarity
    icon: str
    name: str
    sub_category: SubCategory | None
    tags: list[str]


@dataclass(frozen=True)
class Student:
    id: int
    name: str
    # icon: str
    hasBondGear: bool
    StarGrade: int
    DefaultOrder: int
    # Striker ("Main") or Special ("Support")
    SquadType: str
    # For Dual Style Characters
    StyleId: int | None
    LinkedCharacterId: int | None
    # Group them
    BulletType: str
    ArmorType: str
    School: str
    Club: str
    # WeaponImg: str
    # CollectionBG: str


@dataclass(frozen=True)
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str


@dataclass(frozen=True)
class Currency:
    id: int
    rarity: Rarity
    icon: str
    name: str
    desc: str


# ? Will use it on future idk
# @dataclass(frozen=True)
# class ReleaseStatus:
#     jp: bool = False
#     en: bool = False
#     cn: bool = False
