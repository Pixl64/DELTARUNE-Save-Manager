import os
from tkinter import Frame, Label
from tkinter.constants import LEFT, NW, TOP
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.gui_utils import setWindowIcon
from src.widgets.w_selectors import (
    ActiveSaveLocationSelectorFrame,
    BackupSaveLocationSelectorFrame,
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
        setWindowIcon(self)
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
            entryWidth=self.entryWidth,
        )
        self.activeSaveFrame = ActiveSaveLocationSelectorFrame(
            self.mainFrame,
            self.initialDir,
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
            "runGameFollowsActiveChapter": False,
        }
        return
