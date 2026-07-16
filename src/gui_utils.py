import ctypes
import json
import os
import tempfile
from tkinter import Tk, Toplevel

from src.config_load import loadUserConfig
from src.file_utils import copyFile, launch_game
from src.popup.game_select import GameSelectPopup


def setWindowIcon(window: Tk | Toplevel) -> None:
    """Sets the window icon to the icon.ico file in the data directory"""
    # Copy the icon to a temporary directory to avoid issues with tkinter's iconbitmap
    # This is necessary because tkinter's iconbitmap does not work with frozen executables
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        iconSrc = os.path.join(os.environ["DSM_DATA_PATH"], "icon.ico")
        iconTmp = os.path.join(tempDir, "icon_temp.ico")
        copyFile(iconSrc, iconTmp)
        window.iconbitmap(iconTmp)


def set_window_middle(window: Tk, width: int, height: int) -> None:
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    middle = screensize[0] // 2, screensize[1] // 2
    add = middle[0] - width // 2, middle[1] - height // 2
    window.geometry(f"{width}x{height}+{add[0]}+{add[1]}")


def ui_launchGame(
    window: Tk,
    appConfig: dict,
    userConfig: dict,
    chapter: Optional[int] = None,
) -> None:
    if os.environ["DR_EXE_PATH"] == "NOT_SET":
        popup = GameSelectPopup(window)
        if not popup.result:
            return

        # Save the path to user_config.json
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "r") as f:
            userConfig = json.load(f)
        userConfig["launchData"] = popup.result["launchData"]
        userConfig["runGameFollowsActiveChapter"] = popup.result.get(
            "runGameFollowsActiveChapter", False
        )
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(userConfig, f, indent=4)
        # Reload the userConfig from the file to ensure it is up to date
        userConfig = loadUserConfig()

    launch_game(appConfig, userConfig, chapter)
