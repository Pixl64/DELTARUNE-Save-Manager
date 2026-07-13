from src.utils import get_item_name


def add_change(changes, category, label, old, new, dw_invItems=None, item_type=None):
    """Add a change entry. Converts item IDs to names when item_type is provided."""
    if old != new:
        if item_type and dw_invItems:
            old = get_item_name(dw_invItems, old, item_type)
            new = get_item_name(dw_invItems, new, item_type)

        changes[category].append(f'{label}: "{old}" → "{new}"')


def generateCategorizedChangeReport(original, current, dw_invItems, chapterData):
    """Generate a categorized dictionary of changes between original and current data."""

    changes = {
        "Party Equipment Changes": [],
        "Weapon & Armor Inventory Changes": [],
        "Key Item Changes": [],
        "Item & Storage Changes": [],
        "Save Stat Changes": [],
    }

    # Party equipment changes
    equipment_types = {"weapon": "weapon", "armor1": "armor", "armor2": "armor"}

    # Save stats
    save_stats = {
        "darkDollar": "Dark Dollars",
        "floweryDollars": "Flowery Dollars",
        "pinkCoins": "Pink Coins",
        "points": "Points",
    }

    for character in chapterData["dw_partyMemberLocation"].keys():
        for slot, item_type in equipment_types.items():
            add_change(
                changes,
                "Party Equipment Changes",
                f"{character.capitalize()} {slot.capitalize()}",
                original["party"][character][slot],
                current["party"][character][slot],
                dw_invItems,
                item_type,
            )

        # HP changes
        add_change(
            changes,
            "Save Stat Changes",
            f"{character.capitalize()} Current HP",
            original["party"][character].get("currentHP"),
            current["party"][character].get("currentHP"),
        )

        add_change(
            changes,
            "Save Stat Changes",
            f"{character.capitalize()} Max HP",
            original["party"][character].get("maxHP"),
            current["party"][character].get("maxHP"),
        )

    # Weapon inventory
    for i in range(min(len(original["weapons"]), len(current["weapons"]))):
        add_change(
            changes,
            "Weapon & Armor Inventory Changes",
            f"Weapon Slot {i + 1}",
            original["weapons"][i],
            current["weapons"][i],
            dw_invItems,
            "weapon",
        )

    # Armor inventory
    for i in range(min(len(original["armor"]), len(current["armor"]))):
        add_change(
            changes,
            "Weapon & Armor Inventory Changes",
            f"Armor Slot {i + 1}",
            original["armor"][i],
            current["armor"][i],
            dw_invItems,
            "armor",
        )

    # Key items
    for i in range(min(len(original["keyItems"]), len(current["keyItems"]))):
        add_change(
            changes,
            "Key Item Changes",
            f"Key Item Slot {i + 1}",
            original["keyItems"][i],
            current["keyItems"][i],
            dw_invItems,
            "keyItem",
        )

    # Items
    for i in range(min(len(original["items"]), len(current["items"]))):
        add_change(
            changes,
            "Item & Storage Changes",
            f"Item Slot {i + 1}",
            original["items"][i],
            current["items"][i],
            dw_invItems,
            "item",
        )

    # Storage
    if "storage" in original and "storage" in current:
        for i in range(min(len(original["storage"]), len(current["storage"]))):
            add_change(
                changes,
                "Item & Storage Changes",
                f"Storage Slot {i + 1}",
                original["storage"][i],
                current["storage"][i],
                dw_invItems,
                "item",
            )

    for key, label in save_stats.items():
        add_change(
            changes, "Save Stat Changes", label, original.get(key), current.get(key)
        )

    return changes
