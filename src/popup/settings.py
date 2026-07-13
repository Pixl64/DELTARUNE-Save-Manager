import json
import os
from tkinter import Frame, Label
from tkinter.constants import LEFT, NW, TOP
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.widgets.w_selectors import (
    ActiveSaveLocationSelectorFrame,
    BackupSaveLocationSelectorFrame,
    GameSelectSelectorFrame,
)


class SettingsPopup(Dialog):
    def __init__(self, parent, title="", initialDir="."):
        self.FileDialogueTitle = title
        self.initialDir = initialDir
        self.entryWidth = 40

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)

        self.mainFrame = Frame(master)
        self.descriptionLabel = Label(
            self.mainFrame, text="Settings menu.", wraplength=350, justify=LEFT
        )

        self.descriptionLabel.pack(side=TOP, anchor=NW, padx=5, pady=5)

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
        self.backupSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.activeSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.gameSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)

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

        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(self.result, f, indent=4)
