import json
import os

from src.file_utils import constructSave
from src.save_encoding import decodeSave, encodeSave
from src.save_ini_management import getINIfor, mergeIni


def backupSave(chapter: int, slot: int, backupPath: str, useComplete: bool = True):
    saveFilePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot}")
    completeSaveFilePath = os.path.join(
        os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot + 3}"
    )

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


def restoreSave(backupPath: str, chapter: int, slot: int):
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
        completeSavePath = os.path.join(
            os.environ["DR_SAVE_PATH"], f"filech{chapter}_{slot + 3}"
        )
        constructSave(completeSavePath, decodeSave(completeSaveData))

    if "dr.ini" in data:
        iniData = data["dr.ini"]
        iniPath = os.path.join(os.environ["DR_SAVE_PATH"], "dr.ini")

        mergeIni(chapter, slot, iniData, iniPath)
