import os, subprocess, json, base64, configparser

from typing import TextIO

class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

def copyFile(src: str, dest: str):
        subprocess.run(
            f'copy "{src}" "{dest}"', 
            shell=True, 
            stdout=subprocess.DEVNULL
        )

def encodeSave(saveFile:TextIO) -> str:
    """
    Encodes a save file, and returns a base64 encoded string. Decoded by `decodeSave`
    """
    # Read save file lines
    fileText = saveFile.readlines()
    # Add line length at the start of the string.
    finalString = f"len\t{len(fileText)}\n"
    # Loop through each line
    for i, line in enumerate(fileText):
        strippedLine = line.strip()
        # Ignore line if it is 0
        if str(strippedLine) == "0":
            pass
        else:
            # Add the line number and value.
            finalString += f"{i}\t{strippedLine}\n"
    
    # b64 encode string
    encoded = base64.b64encode(str(finalString).encode("utf-8")).decode("utf-8")
        
    return encoded

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
    with open(savePath, "w+") as f:
        f.write("\n".join(lines))

def makeINIKey(chapter:int, slot:int) -> str:
    """
    Constructs an INI key based on the chapter and slot.
    """
    return f"G_{chapter}_{slot}" if chapter != 1 else f"G{slot}"

def getINIfor(chapter:int, slot:int, completeFlag:bool=False, encode:bool=False) -> str:
    iniPath = os.path.join(os.environ["DR_SAVE_PATH"], f"dr.ini")
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
        # Find value that corresponds to the selected chapter and slot
        if f"{chapter}_{slot}" in uraData:
            uraValue = uraData[f"{chapter}_{slot}"]
            iniFile.append(f"{chapter}_0={uraValue}")
    
    finalString = "\n".join(iniFile)
    if encode:
        return base64.b64encode(finalString.encode("utf-8")).decode("utf-8")
    else:
        return finalString

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
    
    # Create the new INI section if it doesn't exist
    if iniKey not in newIniDataParser:
        newIniDataParser.add_section(iniKey)
        # Copy the data from the section chapter `chapter` and slot 0
        # Find the section in newIniDataParser that matches [G_{chapter}_0]
        source_section = f'G_{newChapter}_0'
        if newIniDataParser.has_section(source_section):
            for key, value in newIniDataParser.items(source_section):
                newIniDataParser[iniKey][key] = value
        # Delete the source section to avoid duplication
        newIniDataParser.remove_section(source_section)
        
    # Check if G_{newChapter}_3 exists
    if f"G_{newChapter}_3" in newIniDataParser:
        # Create the complete section if it doesn't exist
        if iniKeyComplete not in newIniDataParser:
            newIniDataParser.add_section(iniKeyComplete)
            # Copy the data from the section chapter `chapter` and slot 3
            source_section_complete = f'G_{newChapter}_3'
            if newIniDataParser.has_section(source_section_complete):
                for key, value in newIniDataParser.items(source_section_complete):
                    newIniDataParser[iniKeyComplete][key] = value
            # Delete the source section to avoid duplication
            newIniDataParser.remove_section(source_section_complete)
    
    # Change the URA section from {chapter}_0 to {newChapter}_{newSlot}
    if "URA" in newIniDataParser:
        uraKey = f"{newChapter}_{newSlot}"
        # Set the value for {newChapter}_{newSlot} in mergeIniParser["URA"] to the value of {chapter}_0 in newIniDataParser["URA"]
        if f"{newChapter}_0" in newIniDataParser["URA"]:
            uraValue = newIniDataParser["URA"][f"{newChapter}_0"]
            if "URA" not in newIniDataParser:
                newIniDataParser.add_section("URA")
            newIniDataParser["URA"][uraKey] = uraValue
    
    # Load the current INI file
    mergeIniParser = CaseSensitiveConfigParser()
    mergeIniParser.read(currentIniFile)
    
    # Clear the existing data for the chapter and slot
    iniKey = makeINIKey(newChapter, newSlot)
    iniKeyComplete = makeINIKey(newChapter, newSlot+3)
    
    if iniKey in mergeIniParser:
        # Remove old section
        mergeIniParser.remove_section(iniKey)
    # Add the new data to the INI file
    mergeIniParser.add_section(iniKey)
    for key, value in newIniDataParser[iniKey].items():
        mergeIniParser[iniKey][key] = value
    
    if iniKeyComplete in newIniDataParser:
        if iniKeyComplete in mergeIniParser:
            # Remove old section
            mergeIniParser.remove_section(iniKeyComplete)
        # Add the new data to the INI file
        mergeIniParser.add_section(iniKeyComplete)
        for key, value in newIniDataParser[iniKeyComplete].items():
            mergeIniParser[iniKeyComplete][key] = value
            
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
    res = {}
    
    # Check if save file is real
    if not os.path.exists(saveFilePath):
        raise FileNotFoundError(f"Save file filech{chapter}_{slot} does not exist.")
    
    # Get save file
    with open(saveFilePath, "r", encoding="UTF-8") as f:
        saveFile = encodeSave(f)
        res[f"filech{chapter}_0"] = saveFile
    
    
    completeFlag = False
    # Get complete save file, if it exists.
    if os.path.exists(completeSaveFilePath) and useComplete:
        with open(completeSaveFilePath, "r", encoding="UTF-8") as f:
            completeSaveFile = encodeSave(f)
        res[f"filech{chapter}_3"] = completeSaveFile
        completeFlag = True
        
    # Get ini information.
    iniData = getINIfor(chapter, slot, completeFlag=completeFlag, encode=True)
    res["dr.ini"] = iniData
    
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
        
def getActiveDisplayData(chapter:int, appconfig:dict) -> dict:
    drSavePath = os.environ["DR_SAVE_PATH"]
    
    # Get relevant files and sort
    files = os.listdir(drSavePath)
    saves = [f for f in files if f.startswith(f"filech{chapter}_") or f == "dr.ini"]
    saves.sort()  
    # Get the save data for the chapter.
    if f"chapter{chapter}" not in appconfig:
        raise ValueError(f"No configuration found for chapter {chapter}.")
    
    saveData = appconfig[f"chapter{chapter}"]
    
    result = {
        "strings": [],
        "slotData":[
            # {
            #   "isComplete": True|False
            # },
            {},{},{},
        ],
    }
    # Select correct room ID adjustment
    match chapter:
        case 1: adjust = 10000
        case 2: adjust = 20000
        case _: adjust = 0
    
    for saveSlot in range(3):
        if f"filech{chapter}_{saveSlot}" in saves:
            with open(os.path.join(drSavePath, f"filech{chapter}_{saveSlot}")) as f:
                # Get room ID from save file. from the line number stored in config[chapter][roomIDLineNumber]
                lines = f.readlines()
                roomIdLineNumber = saveData["roomIDLineNumber"]
                roomId = int(lines[roomIdLineNumber-1].strip())
                
                result["slotData"][saveSlot]["exists"] = True
                
                # Adjust for DELTARUNEdemo to DELTARUNE room IDs.
                if roomId < 9999:
                    roomId += adjust
                
                if str(roomId) in saveData["roomNames"]:
                    roomName = saveData["roomNames"][str(roomId)]
                else:
                    # For some reason chapter 2 doesn't like to use the right room ID. Hopefully this fixes it.
                    if chapter == 2:
                        # See if the room ID is one higher or lower than the one in the config.
                        if str(roomId - 1) in saveData["roomNames"]:
                            roomName = saveData["roomNames"][str(roomId - 1)]
                        elif str(roomId + 1) in saveData["roomNames"]:
                            roomName = saveData["roomNames"][str(roomId + 1)]
                        else:
                            # Try 2 higher or lower.
                            if str(roomId - 2) in saveData["roomNames"]:
                                roomName = saveData["roomNames"][str(roomId - 2)]
                            elif str(roomId + 2) in saveData["roomNames"]:
                                roomName = saveData["roomNames"][str(roomId + 2)]
                            else:
                                # Give up and set to unknown.
                                roomName = "Unknown Room"
                    else:
                        roomName = "Unknown Room"
                # Check for completed save file.
                if os.path.exists(os.path.join(drSavePath, f"filech{chapter}_{saveSlot+3}")):
                    completed = True
                    result["slotData"][saveSlot]["isComplete"] = True
                else:
                    completed = False
                    result["slotData"][saveSlot]["isComplete"] = False
                result["strings"].append(f"Slot {saveSlot + 1}: [{roomName}] {' ★' if completed else ''}")
                    
        else:
            result["strings"].append(f"Slot {saveSlot + 1}: [EMPTY]")
            result["slotData"][saveSlot]["exists"] = False
                
    return result