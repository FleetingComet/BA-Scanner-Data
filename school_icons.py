from constant import SCHOOL_ICON_ALIASES


def normalize_school(value: str) -> str:
    print(f"School debug: {value}")
    return "".join(value.casefold().split())


NO_SCHOOL_IMAGE = ["26011"]  # Saten Ruiko


def get_school_icon(school: object, student_id: object = None) -> str | None:
    """Derive a prospective asset name, without a fixed list of schools.

    Availability is verified by the downloader: a missing school icon uses ETC.
    """
    if str(student_id) in NO_SCHOOL_IMAGE:
        return "ETC"
    if not isinstance(school, str) or not school.strip():
        return None
    name = school.strip()
    key = normalize_school(name)
    return SCHOOL_ICON_ALIASES.get(key, "".join(name.split()))
