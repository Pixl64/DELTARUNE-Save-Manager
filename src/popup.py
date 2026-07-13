import json
import os
from tkinter import Entry, Frame, Label, StringVar
from tkinter.constants import LEFT, NW, TOP
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.widgets import (
    ActiveSaveLocationSelectorFrame,
    BackupFrame,
    BackupSaveLocationSelectorFrame,
    GameSelectSelectorFrame,
    setWindowIcon,
)


class FirstTimeSetup(Dialog):
    def __init__(self, parent, title="", initialDir="."):
        self.FileDialogueTitle = title
        self.initialDir = initialDir
        self.entryWidth = 40

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        setWindowIcon(self.winfo_toplevel())  # pyright: ignore[reportArgumentType]
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)

        self.mainFrame = Frame(master)

        self.descriptionLabel = Label(
            self.mainFrame,
            text="This seems to be the first time you are running this program. Please complete the steps below.",
            wraplength=350,
            justify=LEFT,
        )

        self.backupSaveFrame = BackupSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
            text="Backup Save Location",
            entryWidth=self.entryWidth,
        )
        self.activeSaveFrame = ActiveSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
            text="Active Save Location",
            entryWidth=self.entryWidth,
        )

        self.descriptionLabel.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.backupSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.activeSaveFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)

        self.mainFrame.pack()

    # Function to validate the input
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

        return True

    # Function that is called when the dialog is closed
    def apply(self):
        self.result = {
            "backupSaveLocation": self.backupSaveFrame.getValue(),
            "activeSaveLocation": self.activeSaveFrame.getValue(),
            "hasSeenEditWarning": False,
        }
        return


class GameSelectPopup(Dialog):
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
            self.mainFrame,
            text="Please select the DELTARUNE game location.",
            wraplength=350,
            justify=LEFT,
        )

        self.gameSelectFrame = GameSelectSelectorFrame(
            self.mainFrame,
            self.initialDir,
            text="Game Save Location",
            entryWidth=self.entryWidth,
        )
        self.descriptionLabel.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.gameSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)

        self.mainFrame.pack()

    def validate(self):
        if self.gameSelectFrame.selectedOption.get() == 2:
            if not os.path.exists(self.gameSelectFrame.exePath):
                showerror(
                    title="Error",
                    message=f"Game exacutable location does not exist.\n{self.gameSelectFrame.exePath}",
                )
                return False

        return True

    def apply(self):
        self.result = {"launchData": self.gameSelectFrame.getValue()}
        return


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
            text="Backup Save Location",
            entryWidth=self.entryWidth,
        )
        self.activeSaveFrame = ActiveSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
            text="Active Save Location",
            entryWidth=self.entryWidth,
        )
        self.gameSelectFrame = GameSelectSelectorFrame(
            self.mainFrame,
            self.initialDir,
            text="Game Executable Location",
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
            if not os.path.exists(self.gameSelectFrame.exePath):
                showerror(
                    title="Error",
                    message=f"Game Executable Location does not exist.\n{self.gameSelectFrame.exePath}",
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


class BackupCreatePopup(Dialog):
    def __init__(
        self, parent, chapter: int, config: dict, title: str = "", saveDir: str = "."
    ):
        self.FileDialogueTitle = title
        self.saveDirBase = saveDir
        self.saveDirCurrent = str(saveDir)
        self.entryWidth = 40
        self.config = config
        self.chapter = chapter

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)

        self.mainFrame = Frame(master)

        self.descriptionLabel = Label(
            self.mainFrame,
            text="Please select the location where you want to\ncreate the backup for the current save.",
            wraplength=350,
            justify=LEFT,
        )
        self.backupFrame = BackupFrame(
            self.mainFrame, self.config, newFolderEnabled=True, hideSaves=True
        )
        self.backupFrame.setChapter(self.chapter)

        self.backupNameLabel = Label(self.mainFrame, text="Backup Name:")
        self.backupName = StringVar()
        self.backupNameEntry = Entry(
            self.mainFrame, textvariable=self.backupName, width=self.entryWidth
        )

        self.descriptionLabel.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.backupFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.backupNameLabel.pack(side=TOP, anchor=NW, padx=5)
        self.backupNameEntry.pack(side=TOP, anchor=NW, padx=5)

        self.mainFrame.pack(side=TOP, anchor=NW, padx=5)

    def validate(self):
        invalidChars = r'\/:*?"<>|'
        selectedFolder = self.backupFrame.getSelectedFolder()
        # Check if the backup name is empty
        if not self.backupName.get().strip():
            showerror(title="Error", message="Backup name cannot be empty.")
            return False
        # Check if the backup name contains invalid characters
        if any(char in self.backupName.get() for char in invalidChars):
            showerror(
                title="Error",
                message=f"Backup name cannot contain the following characters: {invalidChars}",
            )
            return False
        # Check if the save file already exists
        if selectedFolder == -1:
            selectedPath = self.backupFrame.currentPath
        else:
            selectedPath = selectedFolder["selectedPath"]

        selectedSaveFileName = self.backupName.get().strip() + ".drsave"
        if os.path.exists(os.path.join(selectedPath, selectedSaveFileName)):
            showerror(
                title="Error",
                message=f"A save file with the name '{selectedSaveFileName}' already exists in the selected directory.",
            )
            return False

        return True

    def apply(self):
        selectedFolder = self.backupFrame.getSelectedFolder()
        if selectedFolder == -1:
            selectedPath = self.backupFrame.currentPath
        else:
            selectedPath = selectedFolder["selectedPath"]

        saveFileLocation = os.path.join(
            selectedPath, self.backupName.get().strip() + ".drsave"
        )

        self.result = {"saveLocation": saveFileLocation}

        return
