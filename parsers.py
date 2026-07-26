from shapes import Equipment, Item, Rarity, Student


def parse_item(item: dict) -> Item:
    return Item(
        id=int(item["Id"]),
        name=item["Name"],
        rarity=Rarity(item["Rarity"]),
        icon=item["Icon"],
    )


def parse_student(item: dict) -> Student:
    return Student(
        id=int(item["Id"]),
        name=item["Name"],
        icon=item["Icon"],
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
