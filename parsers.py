from shapes import Category, Currency, Equipment, Item, Rarity, Student, SubCategory

INCLUDED_ITEM_CATEGORIES = {
    Category.CHARACTER_EXP_GROWTH.value,
    Category.MATERIAL.value,
}


EXCLUDED_ITEM_CATEGORIES = {
    Category.COLLECTIBLE.value,
    Category.CONSUMABLE.value,
    Category.COIN.value,
    Category.FAVOR.value,
    Category.SECRET_STONE.value,  # Temporary
}

INCLUDED_ITEM_SUBCATEGORIES = {
    SubCategory.CD_ITEM.value,
    SubCategory.BOOK_ITEM.value,
    SubCategory.ARTIFACT.value,
}

EXCLUDED_ITEM_TAGS = {"hx"}


SPECIAL_ITEM_IDS = {7, 8, 9, 60, 61, 70, 71}
"""
| 7 (Total Assault Coin)
| 8 (Tactical Challenge Coin)
| 9 (Advanced Total Assault Coin)
| 60 (Joint Firing Drill Coin)
| 61 (Bounty Coins)
| 70 (Grand Assault Coin)
| 71 (Advanced Grand Assault Coin).
"""


def should_include_item(item: dict) -> bool:
    if int(item["Id"]) in SPECIAL_ITEM_IDS:
        return True

    if any(tag.casefold() in EXCLUDED_ITEM_TAGS for tag in (item.get("Tags") or [])):
        return False

    category = item.get("Category")

    if category in EXCLUDED_ITEM_CATEGORIES:
        return False

    return (
        category in INCLUDED_ITEM_CATEGORIES
        or item.get("Subcategory") in INCLUDED_ITEM_SUBCATEGORIES
    )


def parse_item(item: dict) -> Item:
    return Item(
        id=int(item["Id"]),
        category=Category(item["Category"]),
        rarity=Rarity(item["Rarity"]),
        icon=item["Icon"],
        name=item["Name"],
        sub_category=(
            SubCategory(item["Subcategory"])
            if item.get("Subcategory") in SubCategory._value2member_map_
            else None
        ),
        tags=item.get("Tags") or [],
    )


def parse_student(item: dict) -> Student:
    gear = item.get("Gear", {})

    return Student(
        id=int(item["Id"]),
        name=item["Name"],
        # icon=f"/images/student/collection/{int(item["Id"])}.webp",
        hasBondGear=bool(gear),
        StarGrade=item["StarGrade"],
        DefaultOrder=item["DefaultOrder"],
        SquadType=item["SquadType"],
        StyleId=item.get("StyleId"),
        LinkedCharacterId=item.get("LinkedCharacterId"),
        BulletType=item["BulletType"],  # Attack Type
        ArmorType=item["ArmorType"],
        School=item["School"],
        Club=item["Club"],
    )


def parse_equipment(item: dict) -> Equipment:
    return Equipment(
        id=int(item["Id"]),
        category=item["Category"],
        rarity=Rarity(item["Rarity"]),
        tier=int(item["Tier"]),
        icon=item["Icon"],
        name=item["Name"],
    )


def parse_currency(item: dict) -> Currency:
    return Currency(
        id=int(item["Id"]),
        rarity=Rarity(item["Rarity"]),
        icon=item["Icon"],
        name=item["Name"],
        desc=item.get("Desc") or item.get("Description") or "",
    )
