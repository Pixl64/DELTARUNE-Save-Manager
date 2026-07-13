import json
import os
import shutil
import sys
from tkinter import Tk
from typing import Any, Callable, Dict


def copyFile(src: str, dest: str):
    shutil.copy2(src, dest)


def getCurrentWorkingDirectory() -> tuple[str, str, Callable[[], None]]:
    """Returns the current working directory."""
    # Get current running directory
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dataPath = sys._MEIPASS  # type: ignore
        runningDir = os.path.dirname(sys.executable)
        os.chdir(runningDir)

        # Import the pyi_splash module to close the splash screen
        import pyi_splash  # type: ignore

        def killSplash() -> None:
            pyi_splash.close()
    else:
        runningDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        dataPath = runningDir

        def killSplash() -> None:
            pass

    print(f"Running directory: {runningDir}")
    print(f"Data path: {dataPath}")

    return runningDir, dataPath, killSplash


def setUpDirectories(appConfig: Dict[str, Any]) -> None:
    """Sets up the chapter directories in the backup path"""
    for i in range(appConfig["maximumChapter"]):
        if not os.path.exists(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i + 1}")):
            os.mkdir(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i + 1}"))


def validateFiles(runningDir: str, killSplash: Callable) -> bool:
    """Validates the existence of the app_config.json and user_config.json files, and creates the user_config.json if it does not exist."""
    from src.popup.first_time_setup import FirstTimeSetup

    # Check for userconfig
    if not os.path.exists(os.path.join(os.environ["DSM_PATH"], "user_config.json")):
        tempW = Tk()
        tempW.withdraw()
        killSplash()
        print("Running first time setup...")
        data = FirstTimeSetup(tempW, title="Select Directory", initialDir=runningDir)
        if not data.result:
            return False
        tempW.destroy()
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(data.result, f, indent=4)

    return True


def constructSave(savePath: str, lines: list):
    with open(savePath, "w") as f:
        f.write("\n".join(lines))
