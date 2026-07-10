import re
from typing import Dict

# Maps item tag names to categories used in `dw_invItems`
CATEGORY_MAP = {
    "item": "items",
    "keyItem": "keyItems",
    "weapon": "weapons",
    "armor": "armor",
}

def format_item_type(item_tag: str) -> str:
    """Convert camelCase item tag to Title Case (e.g., 'keyItem' -> 'Key Item')."""
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', item_tag).title()

def get_item_name(dw_invItems: Dict[str, Dict[str, str]], item_id, tag: str) -> str:
    """Return display name for an item id and tag; fall back to a placeholder."""
    if item_id is None:
        return f"Unknown {tag} (None)"
    category = CATEGORY_MAP.get(tag, "items")
    item_dict = dw_invItems.get(category, {})
    return item_dict.get(str(item_id), f"Unknown {tag} ({item_id})")

def _item_in_ranges(item_value: int, ranges) -> bool:
    for item_range in ranges:
        if not item_range:
            continue
        if len(item_range) == 1:
            if item_value == item_range[0]:
                return True
            continue

        start, end = sorted(item_range[:2])
        if start <= item_value <= end:
            return True
    return False

def get_chapter_for_item(chapterLimits: dict, item_id: int, item_type: str) -> int:
    """Determine which chapter an item was added in based on chapter limits config."""
    item_id_int = int(item_id)
    type_key = "item" if item_type == "items" else item_type

    chapter_limits = []
    for chapter_num in range(1, 8):
        chapter_key = f"chapter{chapter_num}"
        if chapter_key in chapterLimits:
            chapter_data = chapterLimits[chapter_key]
            if "dw_invItemIdLimit" in chapter_data and type_key in chapter_data["dw_invItemIdLimit"]:
                chapter_limits.append((chapter_num, chapter_data["dw_invItemIdLimit"][type_key]))

    chapter_limits.sort()
    for chapter_num, limits in chapter_limits:
        if _item_in_ranges(item_id_int, limits):
            return chapter_num

    return chapter_limits[-1][0] if chapter_limits else 1

def filter_and_group_items_by_chapter(available_items: dict, chapterLimits: dict, current_chapter: int, item_tag: str) -> Dict[int, list]:
    """Return a dict mapping chapter -> list of (id, name) for items up to current chapter."""
    filtered = {}
    for itemId, itemName in available_items.items():
        item_id_int = int(itemId)
        if item_id_int == 0:
            continue
        item_chapter = get_chapter_for_item(chapterLimits, itemId, item_tag)
        if item_chapter <= current_chapter:
            filtered.setdefault(item_chapter, []).append((item_id_int, itemName))

    # sort ids within chapters
    for ch in filtered:
        filtered[ch].sort(key=lambda x: x[0])

    return dict(sorted(filtered.items()))
