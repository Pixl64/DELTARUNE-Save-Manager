from tkinter import Button, Entry, Frame, IntVar, LabelFrame, Radiobutton, StringVar
from tkinter.constants import DISABLED, NORMAL, N, W

from src.utils import createCutPath, openFilePicker, openFolderPicker


class BackupSaveLocationSelectorFrame(LabelFrame):
    def __init__(self, parent, initialDir: str, *args, entryWidth: int = 40, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.entryWidth = entryWidth
        self.initialDir = initialDir

        self.dirDisplay = StringVar(value="[Nothing Selected]")
        self.saveDir = ""
        self.dirEntry = Entry(
            self, width=self.entryWidth, textvariable=self.dirDisplay, state=DISABLED
        )
        self.selectButton = Button(self, text="Select", command=self.selectBackupFolder)
        self.dirEntry.grid(column=0, row=0, padx=(5, 2.5), pady=(0, 5))
        self.selectButton.grid(column=1, row=0, padx=(2.5, 5), pady=(0, 5))

    def selectBackupFolder(self):
        result = openFolderPicker(
            "Select the backup save location: ",
            initialDir=self.initialDir,
            entryWidth=self.entryWidth,
        )
        if not result:
            return
        self.saveDir = result[0]
        self.dirDisplay.set(result[1])

    def getValue(self):
        return self.saveDir

    def setValue(self, value: str):
        if not value:
            return
        self.saveDir = value
        self.dirDisplay.set(createCutPath(value, self.entryWidth))


class ActiveSaveLocationSelectorFrame(LabelFrame):
    def __init__(self, parent, initialDir: str, *args, entryWidth: int = 40, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.entryWidth = entryWidth
        self.initialDir = initialDir

        # Radio buttons to select option 1, use the default appdata location (most people should use this).
        self.selectedOption = IntVar()
        self.defaultLocation = Radiobutton(
            self,
            text="Default ( %localappdata%\\DELTARUNE )",
            variable=self.selectedOption,
            value=1,
            command=self.sel,
        )
        self.defaultLocation.grid(row=1, sticky=W)

        # Radio buttons to select option 2, use a custom appdata location (most people won't use this).
        self.customLocation = Radiobutton(
            self,
            text="Custom Location",
            variable=self.selectedOption,
            value=2,
            command=self.sel,
        )
        self.customLocation.grid(row=2, sticky=W)

        self.entryFrame = Frame(self)
        self.dirDisplay = StringVar(value="[Nothing Selected]")
        self.saveDir = ""
        self.dirEntry = Entry(
            self.entryFrame, textvariable=self.dirDisplay, width=self.entryWidth
        )
        self.selectButton = Button(
            self.entryFrame, text="Select", command=self.selectActiveFolder
        )
        self.dirEntry.grid(column=0, row=0, padx=(5, 2.5), pady=(0, 5))
        self.selectButton.grid(column=1, row=0, padx=(2.5, 5), pady=(0, 5))
        self.entryFrame.grid(row=3, sticky=N)

        # Set the default option to 1
        self.defaultLocation.invoke()

    def selectActiveFolder(self):
        result = openFolderPicker(
            "Select the custom active save location: ",
            initialDir=self.initialDir,
            entryWidth=self.entryWidth,
        )
        if not result:
            return
        self.saveDir = result[0]
        self.dirDisplay.set(result[1])

    # This runs whenever a radiobutton is pressed
    def sel(self):
        # Get the selected option
        match self.selectedOption.get():
            # If the option is 1, disable the file select button and entry
            case 1:
                self.selectButton.config(state=DISABLED)
                self.dirEntry.config(state=DISABLED)
            # If the option is 2, enable the file select button and entry
            case 2:
                self.selectButton.config(state=NORMAL)
                self.dirEntry.config(state=DISABLED)

    def getValue(self):
        match self.selectedOption.get():
            case 1:
                return {"type": "default"}
            case 2:
                return {"type": "custom", "path": self.saveDir}
            case _:
                return {"type": "default"}

    def setValue(self, value: dict):
        if not value:
            return

        if value["type"] == "default":
            self.defaultLocation.invoke()
        elif value["type"] == "custom":
            self.customLocation.invoke()
            self.saveDir = value["path"]
            self.dirDisplay.set(createCutPath(value["path"], self.entryWidth))


class GameSelectSelectorFrame(LabelFrame):
    def __init__(self, parent, initialDir: str, *args, entryWidth: int = 40, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.entryWidth = entryWidth
        self.initialDir = initialDir

        # Radio buttons to select option 1, open the game by using Steam.
        self.selectedOption = IntVar()
        self.defaultLocation = Radiobutton(
            self,
            text="Use Steam Link",
            variable=self.selectedOption,
            value=1,
            command=self.sel,
        )
        self.defaultLocation.grid(row=1, sticky=W)

        # Radio buttons to select option 2, open the game by directly running the file.
        self.customLocation = Radiobutton(
            self,
            text="Custom Location",
            variable=self.selectedOption,
            value=2,
            command=self.sel,
        )
        self.customLocation.grid(row=2, sticky=W)
        self.entryFrame = Frame(self)
        self.exeDisplay = StringVar(value="[Nothing Selected]")
        self.exePath = ""
        self.exeEntry = Entry(
            self.entryFrame, textvariable=self.exeDisplay, width=self.entryWidth
        )
        self.selectButton = Button(
            self.entryFrame, text="Select", command=self.selectGameExecutable
        )
        self.exeEntry.grid(column=0, row=0, padx=(5, 2.5), pady=(0, 5))
        self.selectButton.grid(column=1, row=0, padx=(2.5, 5), pady=(0, 5))
        self.entryFrame.grid(row=3, sticky=N)

        # Set the default option to 1
        self.defaultLocation.invoke()

    def selectGameExecutable(self):
        result = openFilePicker(
            "Select the custom game executable location: ",
            initialDir=self.initialDir,
            entryWidth=self.entryWidth,
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")],
        )
        if not result:
            return
        self.exePath = result[0]
        self.exeDisplay.set(result[1])

    # This runs whenever a radiobutton is pressed
    def sel(self):
        # Get the selected option
        match self.selectedOption.get():
            # If the option is 1, disable the file select button and entry
            case 1:
                self.selectButton.config(state=DISABLED)
                self.exeEntry.config(state=DISABLED)
            # If the option is 2, enable the file select button and entry
            case 2:
                self.selectButton.config(state=NORMAL)
                self.exeEntry.config(state=DISABLED)

    def getValue(self):
        match self.selectedOption.get():
            case 1:
                return {"type": "steam"}
            case 2:
                return {"type": "custom", "path": self.exePath}

    def setValue(self, value: dict):
        if not value:
            return

        if value["type"] == "steam":
            self.defaultLocation.invoke()
        elif value["type"] == "custom":
            self.customLocation.invoke()
            self.exePath = value["path"]
            self.exeDisplay.set(createCutPath(value["path"], self.entryWidth))
