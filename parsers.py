from shapes import Equipment, Item, Rarity, Student


def parse_item(item: dict) -> Item:
    return Item(
        id=int(item["Id"]),
        name=item["Name"],
        rarity=Rarity(item["Rarity"]),
        icon=item["Icon"],
    )


def parse_student(item: dict) -> Student:
    gear = item.get("Gear", {})

    return Student(
        id=int(item["Id"]),
        name=item["Name"],
        # icon=f"/images/student/collection/{int(item["Id"])}.webp",
        hasBondGear=bool(gear),
        StarGrade=item["StarGrade"],
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
