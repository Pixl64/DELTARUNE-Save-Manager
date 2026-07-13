import os


def writeInventoryItems(
    fileLines: list, chapter: int, newData: dict, chapterConfig: dict
):

    invStart = chapterConfig["dw_invStart"] - 1

    if chapter == 1:
        # Chapter 1 save layout:
        #   [item, key item, weapon, armor] * 12

        entryCount = 12
        entriesPerSlot = 4

        for i in range(entryCount):
            offset = invStart + i * entriesPerSlot

            fileLines[offset] = f"{newData['items'][i]}\n"
            fileLines[offset + 1] = f"{newData['keyItems'][i]}\n"
            fileLines[offset + 2] = f"{newData['weapons'][i]}\n"
            fileLines[offset + 3] = f"{newData['armor'][i]}\n"

    else:  # Chapter 2+
        itemCount = chapterConfig["dw_invCount"]["item"]
        weaponCount = chapterConfig["dw_invCount"]["weapon"]

        # Chapter 2+ save layout:
        #   [item, key item] * itemCount
        #   [unused item, unused key item]  # Present in the save but not used by the game.
        #   [weapon, armor] * weaponCount

        itemSectionEnd = invStart + itemCount * 2
        equipmentSectionStart = (
            itemSectionEnd + 2
        )  # Skip the unused item/key item pair.

        # Write items and key items.
        for i in range(itemCount):
            offset = invStart + i * 2

            fileLines[offset] = f"{newData['items'][i]}\n"
            fileLines[offset + 1] = f"{newData['keyItems'][i]}\n"

        # Write weapons and armor.
        for i in range(weaponCount):
            offset = equipmentSectionStart + i * 2

            fileLines[offset] = f"{newData['weapons'][i]}\n"
            fileLines[offset + 1] = f"{newData['armor'][i]}\n"


def writeCharacterEquipment(fileLines: list, newData: dict, chapterConfig: dict):

    # Character data save layout:
    #   +0  Current HP
    #   +1  Maximum HP
    #   +6  Weapon
    #   +7  Armor 1
    #   +8  Armor 2

    for character, location in chapterConfig["dw_partyMemberLocation"].items():
        # Character is not present in this chapter.
        if location[0] == -1:
            continue

        equipment = newData["partyMembers"][character]
        baseOffset = location[0]

        fileLines[baseOffset] = f"{equipment['currentHP']}\n"
        fileLines[baseOffset + 1] = f"{equipment['maxHP']}\n"
        fileLines[baseOffset + 6] = f"{equipment['weapon']}\n"
        fileLines[baseOffset + 7] = f"{equipment['armor1']}\n"
        fileLines[baseOffset + 8] = f"{equipment['armor2']}\n"


def writeCurrencyValues(fileLines: list, newData: dict, chapterConfig: dict):

    if "dw_darkDollarLine" in chapterConfig:
        fileLines[chapterConfig["dw_darkDollarLine"] - 1] = f"{newData['darkDollar']}\n"

    if "dw_floweryDollarsLine" in chapterConfig:
        fileLines[chapterConfig["dw_floweryDollarsLine"] - 1] = (
            f"{newData.get('floweryDollars')}\n"
        )

    if "dw_pinkCoinsLine" in chapterConfig:
        fileLines[chapterConfig["dw_pinkCoinsLine"] - 1] = (
            f"{newData.get('pinkCoins')}\n"
        )

    if "dw_pointsLine" in chapterConfig:
        fileLines[chapterConfig["dw_pointsLine"] - 1] = f"{newData.get('points')}\n"


def writeActiveSaveFile(chapter: int, slot: int, newData: dict, appConfig: dict):
    """
    Write the modified data back to the save file using the same format as extraction.
    """
    # Load save file
    saveFilePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot}")
    with open(saveFilePath, "r") as f:
        fileLines = f.readlines()

    # Ensure all lines end with newline
    for i in range(len(fileLines)):
        if not fileLines[i].endswith("\n"):
            fileLines[i] += "\n"

    chapterConfig = appConfig[f"chapter{chapter}"]

    writeInventoryItems(fileLines, chapter, newData, chapterConfig)
    writeCharacterEquipment(fileLines, newData, chapterConfig)
    writeCurrencyValues(fileLines, newData, chapterConfig)

    # Write the modified content back to the file
    with open(saveFilePath, "w") as f:
        f.writelines(fileLines)
