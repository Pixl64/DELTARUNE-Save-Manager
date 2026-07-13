import configparser
import os
import re
from tkinter.filedialog import askdirectory, askopenfilename
from typing import Dict

# Maps item tag names to categories used in `dw_invItems`
CATEGORY_MAP = {
    "item": "items",
    "keyItem": "keyItems",
    "weapon": "weapons",
    "armor": "armor",
}

CHARACTER_BITS = {
    "kris": 1,
    "susie": 2,
    "ralsei": 4,
    "noelle": 8,
}


class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr


def can_equip(dw_invItems: dict, item_id: int, item_tag: str, character: str):
    if item_tag not in ["weapon", "armor"]:
        return True  # Only weapons and armor have equip restrictions

    category = CATEGORY_MAP.get(item_tag, item_tag)
    equippable = dw_invItems.get(category, {}).get(str(item_id))
    if equippable is None:
        return False

    equip_mask = int(equippable["equip"], 2)

    character_bit = CHARACTER_BITS[character]

    return (equip_mask & character_bit) != 0


def format_item_type(item_tag: str) -> str:
    """Convert camelCase item tag to Title Case (e.g., 'keyItem' -> 'Key Item')."""
    return re.sub(r"(?<!^)(?=[A-Z])", " ", item_tag).title()


def get_item_name(dw_invItems: Dict[str, Dict], item_id, tag: str) -> str:
    """Return display name for an item id and tag; fall back to a placeholder."""
    if item_id is None:
        return f"Unknown {tag} (None)"

    category = CATEGORY_MAP.get(tag, "items")
    item_dict = dw_invItems.get(category, {})

    item = item_dict.get(str(item_id))

    if item is None:
        return f"Unknown {tag} ({item_id})"

    # Key Item format: "1": "Cell Phone"
    if isinstance(item, str):
        return item

    # New format: "1": {"name": "Wood Blade", "equip": "0001"}
    if isinstance(item, dict):
        return item.get("name", f"Unknown {tag} ({item_id})")

    return f"Unknown {tag} ({item_id})"


def find_room_name(roomId: int, saveData: dict, chapter: int) -> str:
    """Helper function to find room name with fallback logic for Chapter 2."""
    roomIdStr = str(roomId)

    if roomIdStr in saveData["roomNames"]:
        return saveData["roomNames"][roomIdStr]

    # Chapter 2 fallback logic - try offsets
    if chapter == 2:
        for offset in [-1, 1, -2, 2]:
            adjusted = str(roomId + offset)
            if adjusted in saveData["roomNames"]:
                return saveData["roomNames"][adjusted]

    return f"Unknown Room {roomId}"


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


def get_chapter_for_item(appConfig: dict, item_id: int, item_type: str) -> int:
    """Determine which chapter an item was added in based on chapter limits config."""
    item_id_int = int(item_id)
    type_key = "item" if item_type == "items" else item_type

    chapter_limits = []
    for chapter_num in range(1, 8):
        chapter_key = f"chapter{chapter_num}"
        if chapter_key in appConfig:
            chapter_data = appConfig[chapter_key]
            if (
                "dw_invItemIdLimit" in chapter_data
                and type_key in chapter_data["dw_invItemIdLimit"]
            ):
                chapter_limits.append(
                    (chapter_num, chapter_data["dw_invItemIdLimit"][type_key])
                )

    chapter_limits.sort()
    for chapter_num, limits in chapter_limits:
        if _item_in_ranges(item_id_int, limits):
            return chapter_num

    return chapter_limits[-1][0] if chapter_limits else 1


def filter_and_group_items_by_chapter(
    available_items: dict, appConfig: dict, current_chapter: int, item_tag: str
) -> Dict[int, list]:
    """Return a dict mapping chapter -> list of (id, name) for items up to current chapter."""
    filtered = {}
    for itemId, itemName in available_items.items():
        item_id_int = int(itemId)
        if item_id_int == 0:
            continue
        item_chapter = get_chapter_for_item(appConfig, itemId, item_tag)
        if item_chapter <= current_chapter:
            if isinstance(itemName, dict):
                display_name = itemName["name"]
            else:
                display_name = itemName

            filtered.setdefault(item_chapter, []).append((item_id_int, display_name))

    # sort ids within chapters
    for ch in filtered:
        filtered[ch].sort(key=lambda x: x[0])

    return dict(sorted(filtered.items()))


def createCutPath(path: str, entryWidth: int):
    """
    Creates a shortened version of the path for display purposes.
    If the path is longer than entryWidth, it will be cut and prefixed with '...'.
    """
    if len(path) > entryWidth:
        return "..." + path[-(entryWidth - 3) :]
    return path


def openFolderPicker(title: str, initialDir: str, entryWidth: int):
    directory = askdirectory(title=title, initialdir=initialDir)
    if not directory:
        return

    return [directory, createCutPath(directory, entryWidth)]


def openFilePicker(title: str, initialDir: str, entryWidth: int, filetypes=None):

    file = askopenfilename(title=title, initialdir=initialDir, filetypes=filetypes)
    if not file:
        return

    return [file, createCutPath(file, entryWidth)]


def deepMerge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deepMerge(result[key], value)
        else:
            result[key] = value

    return result


def getActiveDisplayData(chapter: int, appconfig: dict) -> dict:
    drSavePath = os.environ["DR_SAVE_PATH"]

    if f"chapter{chapter}" not in appconfig:
        raise ValueError(f"No configuration found for chapter {chapter}.")

    saveData = appconfig[f"chapter{chapter}"]
    files = os.listdir(drSavePath)
    saves = [f for f in files if f.startswith(f"filech{chapter}_") or f == "dr.ini"]
    saves.sort()

    result = {
        "strings": [],
        "slotData": [{}, {}, {}],
    }

    # Select correct room ID adjustment
    adjust = {1: 10000, 2: 20000}.get(chapter, 0)

    for saveSlot in range(3):
        saveFile = f"filech{chapter}_{saveSlot}"

        if saveFile not in saves:
            result["strings"].append(f"Slot {saveSlot + 1}: [EMPTY]")
            result["slotData"][saveSlot]["exists"] = False
            continue

        with open(os.path.join(drSavePath, saveFile)) as f:
            lines = f.readlines()
            roomIdLineNumber = saveData["roomIDLineNumber"]
            roomId = int(lines[roomIdLineNumber - 1].strip())

            # Adjust for DELTARUNEdemo to DELTARUNE room IDs
            if roomId < 9999:
                roomId += adjust

            roomName = find_room_name(roomId, saveData, chapter)

            # Check for completed save file
            completed = os.path.exists(
                os.path.join(drSavePath, f"filech{chapter}_{saveSlot + 3}")
            )

            result["slotData"][saveSlot]["exists"] = True
            result["slotData"][saveSlot]["isComplete"] = completed
            result["strings"].append(
                f"Slot {saveSlot + 1}: [{roomName}]{' ★' if completed else ''}"
            )

    return result
