import base64
import os

from src.utils import CaseSensitiveConfigParser


def makeINIKey(chapter: int, slot: int) -> str:
    """
    Constructs an INI key based on the chapter and slot.
    """
    return f"G_{chapter}_{slot}" if chapter != 1 else f"G{slot}"


def getINIfor(
    chapter: int, slot: int, completeFlag: bool = False, encode: bool = False
) -> str:
    iniPath = os.path.join(os.environ["DR_SAVE_PATH"], "dr.ini")
    iniKey = makeINIKey(chapter, slot)
    iniKeyComplete = makeINIKey(chapter, slot + 3)

    parser = CaseSensitiveConfigParser()
    parser.read(iniPath, encoding="utf-8")

    # Get data from specific ini key
    if iniKey not in parser:
        raise ValueError(f"INI key {iniKey} not found in {iniPath}.")
    iniData = parser[iniKey]

    iniFile = []

    iniFile.append(f"[G_{chapter}_0]")
    for key, value in iniData.items():
        iniFile.append(f"{key}={value}")

    if completeFlag:
        if iniKeyComplete not in parser:
            raise ValueError(f"INI key {iniKeyComplete} not found in {iniPath}.")

        completeIniData = parser[iniKeyComplete]
        iniFile.append(f"[G_{chapter}_3]")
        for key, value in completeIniData.items():
            iniFile.append(f"{key}={value}")

    # Get URA data
    if "URA" in parser:
        uraData = parser["URA"]
        iniFile.append("[URA]")
        if f"{chapter}_{slot}" in uraData:
            uraValue = uraData[f"{chapter}_{slot}"]
            iniFile.append(f"{chapter}_0={uraValue}")

    result = "\n".join(iniFile)
    return (
        base64.b64encode(result.encode("utf-8")).decode("utf-8") if encode else result
    )


def mergeIni(newChapter: int, newSlot: int, newIniString: str, currentIniFile: str):
    """
    Merges a new INI string into an existing INI file.
    """

    # Decode the new INI string
    decodedNewIni = base64.b64decode(newIniString).decode("utf-8")
    # Load new INI data
    newIniDataParser = CaseSensitiveConfigParser()
    newIniDataParser.read_string(decodedNewIni)
    # Change sections to the new chapter and slot
    iniKey = makeINIKey(newChapter, newSlot)
    iniKeyComplete = makeINIKey(newChapter, newSlot + 3)

    # Helper function to copy section data
    def copy_section(from_section: str, to_section: str):
        if from_section in newIniDataParser:
            if to_section not in newIniDataParser:
                newIniDataParser.add_section(to_section)
            for key, value in newIniDataParser.items(from_section):
                newIniDataParser[to_section][key] = value
            newIniDataParser.remove_section(from_section)

    # Create the new INI section from slot 0 template
    copy_section(f"G_{newChapter}_0", iniKey)
    # Create the complete section from slot 3 template if it exists
    copy_section(f"G_{newChapter}_3", iniKeyComplete)

    # Update URA section key from slot 0 to the target slot
    if "URA" in newIniDataParser and f"{newChapter}_0" in newIniDataParser["URA"]:
        uraKey = f"{newChapter}_{newSlot}"
        newIniDataParser["URA"][uraKey] = newIniDataParser["URA"][f"{newChapter}_0"]

    # Load the current INI file
    mergeIniParser = CaseSensitiveConfigParser()
    mergeIniParser.read(currentIniFile)

    # Helper function to update or create section
    def update_section(section_key: str):
        if section_key in newIniDataParser:
            if section_key in mergeIniParser:
                mergeIniParser.remove_section(section_key)
            mergeIniParser.add_section(section_key)
            for key, value in newIniDataParser[section_key].items():
                mergeIniParser[section_key][key] = value

    # Update main and complete sections
    update_section(iniKey)
    update_section(iniKeyComplete)

    # Check if the URA section exists and update it
    if "URA" in mergeIniParser:
        uraKey = f"{newChapter}_{newSlot}"
        # Write the URA key to the INI file
        mergeIniParser["URA"][uraKey] = newIniDataParser["URA"].get(uraKey, "0.00")

    # Write the updated INI data back to the file
    with open(currentIniFile, "w", encoding="utf-8") as iniFile:
        for section in mergeIniParser.sections():
            iniFile.write(f"[{section}]\n")
            for key, value in mergeIniParser.items(section):
                iniFile.write(f"{key}={value}\n")
