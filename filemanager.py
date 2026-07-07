import os
import json
import base64
import configparser
import shutil

from typing import TextIO

class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

def copyFile(src: str, dest: str):
    shutil.copy2(src, dest)

def encodeSave(saveFile:TextIO) -> str:
    """
    Encodes a save file, and returns a base64 encoded string. Decoded by `decodeSave`
    """
    fileText = saveFile.readlines()
    finalString = f"len\t{len(fileText)}\n"
    
    for i, line in enumerate(fileText):
        strippedLine = line.strip()
        if strippedLine != "0":
            finalString += f"{i}\t{strippedLine}\n"
    
    return base64.b64encode(finalString.encode("utf-8")).decode("utf-8")

def decodeSave(encoded: str) -> list:
    """
    Decodes a base64 encoded stripped save file, encoded by `encodeSave`
    """
    # Decode from base64
    decoded_str = base64.b64decode(encoded).decode("utf-8")
    lines = decoded_str.splitlines()

    # Check if it is a valid save.
    if not lines or not lines[0].startswith("len\t"):
        raise ValueError("Invalid encoded save format.")

    total_lines = int(lines[0].split("\t")[1])
    # Default to "0" for all lines
    file_lines = ["0"] * total_lines  

    for line in lines[1:]:
        lineNumber, value = line.split("\t", 1)
        file_lines[int(lineNumber)] = value

    return file_lines

def constructSave(savePath:str, lines:list):
    with open(savePath, "w") as f:
        f.write("\n".join(lines))

def makeINIKey(chapter:int, slot:int) -> str:
    """
    Constructs an INI key based on the chapter and slot.
    """
    return f"G_{chapter}_{slot}" if chapter != 1 else f"G{slot}"

def getINIfor(chapter:int, slot:int, completeFlag:bool=False, encode:bool=False) -> str:
    iniPath = os.path.join(os.environ["DR_SAVE_PATH"], "dr.ini")
    iniKey = makeINIKey(chapter, slot)
    iniKeyComplete = makeINIKey(chapter, slot+3)

    parser = CaseSensitiveConfigParser()
    parser.read(iniPath, encoding="utf-8")

    # Get data from specific ini key
    if iniKey not in parser:
        raise ValueError(f"INI key {iniKey} not found in {iniPath}.")
    iniData = parser[iniKey]
    
    iniFile = []
    
    iniFile.append(f'[G_{chapter}_0]')
    for key, value in iniData.items():
        iniFile.append(f"{key}={value}")
    
    if completeFlag:
        if iniKeyComplete not in parser:
            raise ValueError(f"INI key {iniKeyComplete} not found in {iniPath}.")
        
        completeIniData = parser[iniKeyComplete]
        iniFile.append(f'[G_{chapter}_3]')
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
    return base64.b64encode(result.encode("utf-8")).decode("utf-8") if encode else result

def mergeIni(newChapter:int, newSlot:int, newIniString:str, currentIniFile:str):
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
    iniKeyComplete = makeINIKey(newChapter, newSlot+3)
    
    # Helper function to copy section data
    def copy_section(from_section: str, to_section: str):
        if from_section in newIniDataParser:
            if to_section not in newIniDataParser:
                newIniDataParser.add_section(to_section)
            for key, value in newIniDataParser.items(from_section):
                newIniDataParser[to_section][key] = value
            newIniDataParser.remove_section(from_section)
    
    # Create the new INI section from slot 0 template
    copy_section(f'G_{newChapter}_0', iniKey)
    # Create the complete section from slot 3 template if it exists
    copy_section(f'G_{newChapter}_3', iniKeyComplete)
    
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
            iniFile.write(f'[{section}]\n')
            for key, value in mergeIniParser.items(section):
                iniFile.write(f'{key}={value}\n')    

def backupSave(chapter:int, slot:int, backupPath:str, useComplete:bool=True):
    saveFilePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot}")
    completeSaveFilePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot+3}")
    
    if not os.path.exists(saveFilePath):
        raise FileNotFoundError(f"Save file filech{chapter}_{slot} does not exist.")
    
    res = {}
    
    # Get save file
    with open(saveFilePath, "r", encoding="UTF-8") as f:
        res[f"filech{chapter}_0"] = encodeSave(f)
    
    # Get complete save file if it exists
    completeFlag = False
    if useComplete and os.path.exists(completeSaveFilePath):
        with open(completeSaveFilePath, "r", encoding="UTF-8") as f:
            res[f"filech{chapter}_3"] = encodeSave(f)
        completeFlag = True
    
    # Get ini information
    res["dr.ini"] = getINIfor(chapter, slot, completeFlag=completeFlag, encode=True)
    
    with open(backupPath, "w") as f:
        json.dump(res, f, indent=4)
    
    return True

def restoreSave(backupPath:str, chapter:int, slot:int):
    """
    Restores a save from a backup file.
    """
    if not os.path.exists(backupPath):
        raise FileNotFoundError(f"Backup file {backupPath} does not exist.")
    
    with open(backupPath, "r") as f:
        data = json.load(f)
    
    if f"filech{chapter}_0" in data:
        saveData = data[f"filech{chapter}_0"]
        savePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot}")
        constructSave(savePath, decodeSave(saveData))
    
    if f"filech{chapter}_3" in data:
        completeSaveData = data[f"filech{chapter}_3"]
        completeSavePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot+3}")
        constructSave(completeSavePath, decodeSave(completeSaveData))
    
    if "dr.ini" in data:
        iniData = data["dr.ini"]
        iniPath = os.path.join(os.environ["DR_SAVE_PATH"], "dr.ini")
        
        mergeIni(chapter, slot, iniData, iniPath)
        
def _find_room_name(roomId: int, saveData: dict, chapter: int) -> str:
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

def getActiveDisplayData(chapter:int, appconfig:dict) -> dict:
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
            
            roomName = _find_room_name(roomId, saveData, chapter)
            
            # Check for completed save file
            completed = os.path.exists(os.path.join(drSavePath, f"filech{chapter}_{saveSlot+3}"))
            
            result["slotData"][saveSlot]["exists"] = True
            result["slotData"][saveSlot]["isComplete"] = completed
            result["strings"].append(f"Slot {saveSlot + 1}: [{roomName}]{' ★' if completed else ''}")
    
    return result