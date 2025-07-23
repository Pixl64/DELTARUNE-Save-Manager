import os, json

from typing import TextIO

def saveFileItemRead(file:TextIO, chapter:int, config:dict, savePattern:str) -> dict:
    """
    Reads the items from a save file and returns a dictionary of items.
    
    :param file: The file to read from.
    :param limiters: The limiters for the items.
    :param savePattern: The pattern of the save file.

    Valid save patterns:
    - "ch1": For save files with 12 weapon and armor slots (chapter 1)
    - "ch2+": For save files with 48 weapon and armor slots (chapter 2 and onwards)
    
    :return dict: A dictionary with the items, key items, weapons, armor, and storage
    
    """
    
    if f"chapter{chapter}" not in config:
        return -1 
    chapterConfig = config[f"chapter{chapter}"]
    inv_itemNames = config["dw_invItems"]
    
    if savePattern not in ["ch1", "ch2+"]:
        raise ValueError("Invalid save pattern. Must be 'ch1' or 'ch2+'.")
    
    resDict = {
        "party": {
            "kris": {
                "weapon": 0,
                "armor1":0,
                "armor2":0
            },
            "susie": {
                "weapon": 0,
                "armor1":0,
                "armor2":0  
            },
            "ralsei": {
                "weapon": 0,
                "armor1":0,
                "armor2":0
            },
            "noelle": {
                "weapon": 0,
                "armor1":0,
                "armor2":0
            }
        },
        "items": [],
        "keyItems": [],
        "weapons": [],
        "armor": [],
        "storage": []
    }
        
    if savePattern == "ch1":
        fileList = file.readlines()
        start = chapterConfig["dw_invStart"]
        end = chapterConfig["dw_invEnd"]
        items = fileList[start-1:end]
        
        # Check if the item counts match the expected values for chapter 1
        if chapterConfig["dw_invCount"]["item"] != 12 or \
                chapterConfig["dw_invCount"]["keyItem"] != 12 or \
                chapterConfig["dw_invCount"]["weapon"] != 12 or \
                chapterConfig["dw_invCount"]["armor"] != 12:
            raise ValueError("Invalid item count in save file. Expected 12 items, key items, weapons, and armor.")
        
        # Read items, key items, weapons, and armor from the file
        # As this is a chapter 1 save file, 12 items of each is expected.
        for i in range(12):
            resDict["items"].append(inv_itemNames["items"][str(items[i*4].strip())])
            resDict["keyItems"].append(inv_itemNames["keyItems"][str(items[i*4 + 1].strip())])
            resDict["weapons"].append(inv_itemNames["weapons"][str(items[i*4 + 2].strip())])
            resDict["armor"].append(inv_itemNames["armor"][str(items[i*4 + 3].strip())])
            
    if savePattern == "ch2+":
        fileList = file.readlines()
        invStart = chapterConfig["dw_invStart"]
        invEnd = chapterConfig["dw_invEnd"]
        items = fileList[invStart-1:invEnd]
        
        # Check if the item counts match the expected values for chapter 2 and onwards
        if chapterConfig["dw_invCount"]["item"] != chapterConfig["dw_invCount"]["keyItem"]:
            raise ValueError("Invalid item count in save file. Expected equal item and key item counts.")
        
        # Read held items and key items from the file
        itemsAndKeyItems = items[:chapterConfig["dw_invCount"]["item"] * 2]
        for i in range(chapterConfig["dw_invCount"]["item"]):
            resDict["items"].append(inv_itemNames["items"][str(itemsAndKeyItems[i*2].strip())])
            resDict["keyItems"].append(inv_itemNames["keyItems"][str(itemsAndKeyItems[i*2 + 1].strip())])
        
        # Check if the weapon and armor counts match the expected values for chapter 2 and onwards
        if chapterConfig["dw_invCount"]["weapon"] != chapterConfig["dw_invCount"]["armor"]:
            raise ValueError("Invalid weapon and armor count in save file. Expected equal weapon and armor counts.")
        
        # Read weapons and armor from the file
        armorAndWeapons = items[chapterConfig["dw_invCount"]["item"] * 2+2:]
        for i in range(chapterConfig["dw_invCount"]["weapon"]):
            resDict["weapons"].append(inv_itemNames["weapons"][str(armorAndWeapons[i*2].strip())])
            resDict["armor"].append(inv_itemNames["armor"][str(armorAndWeapons[i*2 + 1].strip())])
        
    # If storage is present, read it.
    if "dw_storageStart" in chapterConfig and "dw_storageEnd" in chapterConfig:
        storageStart = chapterConfig["dw_storageStart"]
        storageEnd = chapterConfig["dw_storageEnd"]
        storageLength = chapterConfig["dw_invCount"]["storage"]
        
        # Check if the storage count matches the expected value
        if storageLength != storageEnd - storageStart + 1:
            raise ValueError(f"Invalid storage count in save file. Expected {storageLength} storage items instead of {storageEnd - storageStart + 1}.")
    
        storageItems = fileList[storageStart-1:storageEnd]
        
        # Loop through the storage items and add them to the result dictionary
        if len(storageItems) > 0:
            for item in storageItems:
                resDict["storage"].append(inv_itemNames["items"][str(item.strip())])
    
    return resDict

if __name__ == "__main__":
    import json, os
    runningDir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(runningDir, "app_config.json"), "r", encoding="utf-8") as v:
        cfg = json.load(v)
    with open(r"C:\Users\joehb\AppData\Local\DELTARUNE\filech4_1", "r") as save:
        res = saveFileItemRead(save, 4, cfg, "ch2+")
    with open("res.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=4)