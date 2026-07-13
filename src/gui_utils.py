import ctypes
import json
import os
import tempfile
from tkinter import Tk
from tkinter.messagebox import (
    showerror,
)

from src.config_load import loadUserConfig
from src.file_utils import copyFile
from src.popup.game_select import GameSelectPopup


def setWindowIcon(window: Tk):
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


def launchGame(window: Tk, appConfig: dict) -> None:
    if os.environ["DR_EXE_PATH"] == "NOT_SET":
        popup = GameSelectPopup(window)
        if not popup.result:
            return

        # Save the path to user_config.json
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "r") as f:
            userConfig = json.load(f)
        userConfig["launchData"] = popup.result["launchData"]
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(userConfig, f, indent=4)

        loadUserConfig()  # Reload user config to update the environment variable

    if os.environ["DR_EXE_PATH"] == "VIA_STEAM":
        os.system(f"start steam://rungameid/{appConfig['appID']}")
        return
    if not os.path.exists(os.environ["DR_EXE_PATH"]):
        showerror(
            title="Error",
            message="Game executable path does not exist. Please reset it in the settings.",
        )
        return
    else:
        exe_path = os.environ["DR_EXE_PATH"]

        # Change running directory to where the deltarune executable is otherwise it won't get past chapter select
        os.chdir(os.path.dirname(os.environ["DR_EXE_PATH"]))
        os.startfile(f'"{exe_path}"')
        os.chdir(os.environ["DSM_PATH"])
