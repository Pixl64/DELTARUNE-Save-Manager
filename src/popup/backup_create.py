import os
from tkinter import Entry, Frame, Label, StringVar
from tkinter.constants import LEFT, NW, TOP
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.gui_utils import setWindowIcon
from src.widgets.w_backup_frame import BackupFrame


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
        setWindowIcon(self)
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
