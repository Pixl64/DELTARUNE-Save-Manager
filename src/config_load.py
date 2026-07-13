import json
import os
import tempfile
from typing import Any, Dict

from src.file_utils import copyFile
from src.utils import deepMerge


def loadJsonConfig(fileName: str) -> Dict[str, Any]:
    """Loads a JSON config from the local directory or embedded data directory."""
    localPath = os.path.join(os.environ["DSM_PATH"], fileName)
    if os.path.exists(localPath):
        with open(localPath) as f:
            return json.load(f)

    print(f"{fileName} not found locally. Using embedded config...")
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        configSrc = os.path.join(os.environ["DSM_DATA_PATH"], fileName)
        configTmp = os.path.join(tempDir, fileName)
        copyFile(configSrc, configTmp)
        with open(configTmp) as f:
            return json.load(f)


def loadAppConfig() -> Dict[str, Any]:
    """Loads the application configuration."""

    config = loadJsonConfig("cfg_app.json")
    chapterConfig = loadJsonConfig("cfg_chapter.json")
    roomNames = loadJsonConfig("cfg_room_names.json")
    inventoryItems = loadJsonConfig("cfg_inventory_items.json")

    # Merge default config into chapters
    defaultConfig = chapterConfig.pop("default", {})

    for chapterKey, chapterOverrides in chapterConfig.items():
        mergedConfig = deepMerge(defaultConfig, chapterOverrides)

        # Preserve any existing app-specific values
        if chapterKey in config:
            config[chapterKey] = deepMerge(config[chapterKey], mergedConfig)
        else:
            config[chapterKey] = mergedConfig

    for chapterKey, chapterRooms in roomNames.items():
        if chapterKey in config:
            config[chapterKey]["roomNames"] = chapterRooms

    config["dw_invItems"] = inventoryItems

    return config


def loadUserConfig() -> Dict[str, Any]:
    """Loads the user config from user_config.json and sets the environment variables"""
    with open(os.path.join(os.environ["DSM_PATH"], "user_config.json")) as f:
        config = json.load(f)

    os.environ["DSM_BKP_PATH"] = config["backupSaveLocation"]
    localappdata = os.getenv("LOCALAPPDATA")
    if config["activeSaveLocation"]["type"] == "default":
        os.environ["DR_SAVE_PATH"] = os.path.join(
            localappdata if localappdata else "", "DELTARUNE"
        )
    else:
        os.environ["DR_SAVE_PATH"] = config["activeSaveLocation"]["path"]
    if "launchData" not in config:
        os.environ["DR_EXE_PATH"] = "NOT_SET"
    else:
        if config["launchData"]["type"] == "steam":
            os.environ["DR_EXE_PATH"] = "VIA_STEAM"
        if config["launchData"]["type"] == "custom":
            os.environ["DR_EXE_PATH"] = config["launchData"]["path"]
    return config
