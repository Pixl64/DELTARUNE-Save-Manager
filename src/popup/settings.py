import json
import os
from tkinter import Frame
from tkinter.constants import NW, TOP, X
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.gui_utils import setWindowIcon
from src.widgets.w_buttonbox import ChapterLaunchPatch, OpenFolderButtonBox
from src.widgets.w_selectors import (
    ActiveSaveLocationSelectorFrame,
    BackupSaveLocationSelectorFrame,
    GameSelectSelectorFrame,
)


class SettingsPopup(Dialog):
    def __init__(self, parent, appID, title="", initialDir="."):
        self.FileDialogueTitle = title
        self.initialDir = initialDir
        self.entryWidth = 40
        self.appID = appID

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        setWindowIcon(self)
        self.minsize(width=250, height=100)

        self.mainFrame = Frame(master)

        self.backupSaveFrame = BackupSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
            entryWidth=self.entryWidth,
        )
        self.activeSaveFrame = ActiveSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
            entryWidth=self.entryWidth,
        )
        self.gameSelectFrame = GameSelectSelectorFrame(
            self.mainFrame,
            self.initialDir,
            entryWidth=self.entryWidth,
        )

        self.openFolderButtonBox = OpenFolderButtonBox(self.mainFrame, self.appID)

        self.chapterLaunchPatch = ChapterLaunchPatch(self.mainFrame, self.appID)

        self.backupSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.activeSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.gameSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.openFolderButtonBox.pack(side=TOP, anchor=NW, padx=5, pady=5, fill=X)
        self.chapterLaunchPatch.pack(side=TOP, anchor=NW, padx=5, pady=5, fill=X)

        # Load the current settings from user_config.json
        try:
            with open(
                os.path.join(os.environ["DSM_PATH"], "user_config.json"), "r"
            ) as f:
                userConfig = json.load(f)
            self.backupSaveFrame.setValue(userConfig["backupSaveLocation"])
            self.activeSaveFrame.setValue(userConfig["activeSaveLocation"])
            if "launchData" in userConfig:
                self.gameSelectFrame.setValue(userConfig["launchData"])
            if "runGameFollowsActiveChapter" in userConfig:
                self.gameSelectFrame.setFollowActiveChapter(
                    userConfig["runGameFollowsActiveChapter"]
                )

        except FileNotFoundError:
            showerror(
                title="Error",
                message="User configuration file not found. Please run the application first to create it.",
            )
            return

        self.mainFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)

        self.mainFrame.pack()

    def validate(self):

        if not os.path.exists(self.backupSaveFrame.getValue()):
            showerror(
                title="Error",
                message=f"Backup Save Location does not exist.\n{self.backupSaveFrame.getValue()}",
            )
            return False
        activeSaveData = self.activeSaveFrame.getValue()
        if activeSaveData["type"] == "custom":
            if not os.path.exists(activeSaveData["path"]):
                showerror(
                    title="Error",
                    message=f"Active Save Location does not exist.\n{activeSaveData['path']}",
                )
                return False
        if self.gameSelectFrame.selectedOption.get() == 2:
            gamePath = self.gameSelectFrame.getPath()

            if not os.path.exists(gamePath):
                showerror(
                    title="Error",
                    message=f"Game Executable Location does not exist.\n{gamePath}",
                )
                return False

        return True

    def apply(self):

        self.result = {
            "backupSaveLocation": self.backupSaveFrame.getValue(),
            "activeSaveLocation": self.activeSaveFrame.getValue(),
            "launchData": self.gameSelectFrame.getValue(),
            "runGameFollowsActiveChapter": self.gameSelectFrame.getFollowActiveChapter(),
        }

        # Load the current settings from user_config.json
        try:
            with open(
                os.path.join(os.environ["DSM_PATH"], "user_config.json"), "r"
            ) as f:
                userConfig = json.load(f)
        except FileNotFoundError:
            userConfig = {}

        # Update the userConfig with the new settings
        userConfig["backupSaveLocation"] = self.result["backupSaveLocation"]
        userConfig["activeSaveLocation"] = self.result["activeSaveLocation"]
        userConfig["launchData"] = self.result["launchData"]
        userConfig["hasSeenEditWarning"] = userConfig.get("hasSeenEditWarning", False)
        userConfig["runGameFollowsActiveChapter"] = userConfig.get(
            "runGameFollowsActiveChapter", False
        )

        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(userConfig, f, indent=4)
