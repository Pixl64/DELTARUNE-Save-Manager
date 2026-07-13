import os


def readInventoryItems(fileLines: list, chapter: int, chapterConfig: dict):

    # Extract inventory items from the file based on chapter configuration
    invStart = chapterConfig["dw_invStart"]
    invEnd = chapterConfig["dw_invEnd"]
    invItems = fileLines[invStart - 1 : invEnd]

    items = []
    keyItems = []
    weapons = []
    armor = []

    if chapter == 1:
        # Chapter 1 save layout:
        #   [item, key item, weapon, armor] * 12

        entryCount = 12
        entriesPerSlot = 4

        # Read held items, key items, weapons, and armor.
        for i in range(entryCount):
            offset = i * entriesPerSlot

            items.append(int(invItems[offset].strip()))
            keyItems.append(int(invItems[offset + 1].strip()))
            weapons.append(int(invItems[offset + 2].strip()))
            armor.append(int(invItems[offset + 3].strip()))

    else:  # Chapter 2+
        itemCount = chapterConfig["dw_invCount"]["item"]

        # Chapter 2+ save layout:
        #   [item, key item] * itemCount
        #   [unused item, unused key item]  # Present in the save but not used by the game.
        #   [weapon, armor] * weaponCount

        itemSectionEnd = itemCount * 2
        equipmentSectionStart = (
            itemSectionEnd + 2
        )  # Skip the unused item/key item pair.

        # Read held items and key items.
        itemsAndKeyItems = invItems[:itemSectionEnd]
        for i in range(itemCount):
            items.append(int(itemsAndKeyItems[i * 2].strip()))
            keyItems.append(int(itemsAndKeyItems[i * 2 + 1].strip()))

        # Read weapons and armor.
        armorAndWeapons = invItems[equipmentSectionStart:]
        for i in range(chapterConfig["dw_invCount"]["weapon"]):
            weapons.append(int(armorAndWeapons[i * 2].strip()))
            armor.append(int(armorAndWeapons[i * 2 + 1].strip()))

    return {"items": items, "keyItems": keyItems, "weapons": weapons, "armor": armor}


def readCharacterEquipment(fileLines: list, chapterConfig: dict):
    characterData = {}

    # Character data save layout:
    #   +0  Current HP
    #   +1  Maximum HP
    #   +6  Weapon
    #   +7  Armor 1
    #   +8  Armor 2

    for character, locData in chapterConfig["dw_partyMemberLocation"].items():
        # Character does not exist in this chapter
        if locData[0] == -1:
            continue

        base_idx = locData[0]
        characterData[character] = {
            "currentHP": int(fileLines[base_idx].strip()),
            "maxHP": int(fileLines[base_idx + 1].strip()),
            "weapon": int(fileLines[base_idx + 6].strip()),
            "armor1": int(fileLines[base_idx + 7].strip()),
            "armor2": int(fileLines[base_idx + 8].strip()),
        }
    return characterData


def readStorageItems(fileLines: list, chapterConfig: dict):
    storageItems = []
    storageStart = chapterConfig["dw_storageStart"]
    storageEnd = chapterConfig["dw_storageEnd"]
    storageLength = chapterConfig["dw_invCount"]["storage"]

    # Check if the storage count matches the expected value
    if storageLength != storageEnd - storageStart + 1:
        raise ValueError(
            f"Invalid storage count in save file. Expected {storageLength} storage items instead of {storageEnd - storageStart + 1}."
        )

    storageItems = fileLines[storageStart - 1 : storageEnd]
    return [int(item.strip()) for item in storageItems]


def readCurrencyValues(fileLines: list, chapterConfig: dict):
    currencyValues = {}
    if "dw_darkDollarLine" in chapterConfig:
        darkDollarIdx = chapterConfig["dw_darkDollarLine"] - 1
        currencyValues["darkDollar"] = int(fileLines[darkDollarIdx].strip())

    if "dw_pointsLine" in chapterConfig:
        pointsIdx = chapterConfig["dw_pointsLine"] - 1
        currencyValues["points"] = int(float(fileLines[pointsIdx].strip()))

    if "dw_floweryDollarsLine" in chapterConfig:
        floweryDollarsIdx = chapterConfig["dw_floweryDollarsLine"] - 1
        currencyValues["floweryDollars"] = int(fileLines[floweryDollarsIdx].strip())

    if "dw_pinkCoinsLine" in chapterConfig:
        pinkCoinsIdx = chapterConfig["dw_pinkCoinsLine"] - 1
        currencyValues["pinkCoins"] = int(fileLines[pinkCoinsIdx].strip())

    return currencyValues


def readActiveSaveFile(chapter: int, slot: int, appConfig: dict):
    """
    Reads the active save file for the given chapter and save slot.
    Returns a dictionary containing the save file data.
    """

    # Load save file
    saveFilePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot}")
    with open(saveFilePath, "r") as f:
        fileLines = f.readlines()

    resDict = {
        "party": {
            "kris": {"currentHP": 0, "maxHP": 0, "weapon": 0, "armor1": 0, "armor2": 0},
            "susie": {
                "currentHP": 0,
                "maxHP": 0,
                "weapon": 0,
                "armor1": 0,
                "armor2": 0,
            },
            "ralsei": {
                "currentHP": 0,
                "maxHP": 0,
                "weapon": 0,
                "armor1": 0,
                "armor2": 0,
            },
            "noelle": {
                "currentHP": 0,
                "maxHP": 0,
                "weapon": 0,
                "armor1": 0,
                "armor2": 0,
            },
        },
        "items": [],
        "keyItems": [],
        "weapons": [],
        "armor": [],
        "storage": [],
        "darkDollar": 0,
    }

    chapterConfig = appConfig[f"chapter{chapter}"]

    # Read inventory items & map to resDict
    invItems = readInventoryItems(fileLines, chapter, chapterConfig)
    for key in ("items", "keyItems", "weapons", "armor"):
        resDict[key] = invItems[key]

    # Read character equipment & map to resDict
    charaEquip = readCharacterEquipment(fileLines, chapterConfig)
    for character in resDict["party"]:
        if character in charaEquip:
            resDict["party"][character] = charaEquip[character]

    # If storage is present, read it
    if chapterConfig["dw_invCount"]["storage"] > 0:
        resDict["storage"] = readStorageItems(fileLines, chapterConfig)

    # Read currency values
    currencyValues = readCurrencyValues(fileLines, chapterConfig)
    for valueKey in currencyValues:
        resDict[valueKey] = currencyValues[valueKey]

    return resDict
