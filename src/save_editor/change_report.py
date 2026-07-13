from src.utils import get_item_name


def add_change(changes, category, label, old, new, dw_invItems=None, item_type=None):
    """Add a change entry. Converts item IDs to names when item_type is provided."""
    if old != new:
        if item_type and dw_invItems:
            old = get_item_name(dw_invItems, old, item_type)
            new = get_item_name(dw_invItems, new, item_type)

        changes[category].append(f'{label}: "{old}" → "{new}"')


def add_inventory_changes(
    changes,
    category,
    label_prefix,
    original_items,
    current_items,
    dw_invItems,
    item_type,
):
    """Detect item swaps and report them, otherwise report normal changes."""

    processed = set()

    for i, old_item in enumerate(original_items):
        if i in processed:
            continue

        if old_item != current_items[i]:
            # Look for where the old item moved to
            try:
                old_new_position = current_items.index(old_item)
            except ValueError:
                old_new_position = None

            # Look for where the new item came from
            try:
                new_old_position = original_items.index(current_items[i])
            except ValueError:
                new_old_position = None

            # Check if this is a swap
            if (
                old_new_position is not None
                and new_old_position is not None
                and old_new_position == new_old_position
                and old_new_position != i
                and current_items[old_new_position] == old_item
            ):
                old_name = get_item_name(dw_invItems, old_item, item_type)
                new_name = get_item_name(dw_invItems, current_items[i], item_type)

                changes[category].append(
                    f"{label_prefix} Slots {i + 1} & {old_new_position + 1} swapped: "
                    f'"{old_name}" ↔ "{new_name}"'
                )

                processed.add(i)
                processed.add(old_new_position)
                continue

            add_change(
                changes,
                category,
                f"{label_prefix} Slot {i + 1}",
                old_item,
                current_items[i],
                dw_invItems,
                item_type,
            )


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
    add_inventory_changes(
        changes,
        "Weapon & Armor Inventory Changes",
        "Weapon",
        original["weapons"],
        current["weapons"],
        dw_invItems,
        "weapon",
    )

    # Armor inventory
    add_inventory_changes(
        changes,
        "Weapon & Armor Inventory Changes",
        "Armor",
        original["armor"],
        current["armor"],
        dw_invItems,
        "armor",
    )

    # Key items
    add_inventory_changes(
        changes,
        "Key Item Changes",
        "Key Item",
        original["keyItems"],
        current["keyItems"],
        dw_invItems,
        "keyItem",
    )

    # Items
    add_inventory_changes(
        changes,
        "Item & Storage Changes",
        "Item",
        original["items"],
        current["items"],
        dw_invItems,
        "item",
    )

    # Storage
    if "storage" in original and "storage" in current:
        add_inventory_changes(
            changes,
            "Item & Storage Changes",
            "Storage",
            original["storage"],
            current["storage"],
            dw_invItems,
            "item",
        )

    for key, label in save_stats.items():
        add_change(
            changes, "Save Stat Changes", label, original.get(key), current.get(key)
        )

    return changes
