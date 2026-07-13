import os
import tempfile
from tkinter import (
    Button,
    Entry,
    Frame,
    IntVar,
    Label,
    LabelFrame,
    Listbox,
    Radiobutton,
    Scrollbar,
    Spinbox,
    StringVar,
    Tk,
)
from tkinter.constants import DISABLED, EW, LEFT, NORMAL, NW, RIGHT, TOP, VERTICAL, N, W
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror
from tkinter.simpledialog import askstring
from typing import Callable

from filemanager import copyFile, getActiveDisplayData


def setWindowIcon(window: Tk):
    """Sets the window icon to the icon.ico file in the data directory"""
    # Copy the icon to a temporary directory to avoid issues with tkinter's iconbitmap
    # This is necessary because tkinter's iconbitmap does not work with frozen executables
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        iconSrc = os.path.join(os.environ["DSM_DATA_PATH"], "icon.ico")
        iconTmp = os.path.join(tempDir, "icon_temp.ico")
        copyFile(iconSrc, iconTmp)
        window.iconbitmap(iconTmp)


class ChapterSelectFrame(Frame):
    def __init__(self, parent, appconfig: dict, listBoxUpdateCommand: Callable):
        super().__init__(parent)
        self.parent = parent

        self.chapterLabel = Label(self, text="Chapter: ")
        self.chapterLabel.pack(side=LEFT, anchor=NW)
        self.chapterVariable = IntVar(value=appconfig["defaultChapter"])
        self.chapterSelectSpinbox = Spinbox(
            self,
            from_=1,
            to=appconfig["maximumChapter"],
            width=2,
            wrap=True,
            textvariable=self.chapterVariable,
        )
        self.chapterSelectSpinbox.config(
            command=lambda: listBoxUpdateCommand(self.chapterVariable.get())
        )
        self.chapterSelectSpinbox.pack(side=LEFT, anchor=NW)

    def getChapter(self):
        return self.chapterVariable.get()


class ActiveFrame(Frame):
    def __init__(self, parent, appConfig: dict):
        super().__init__(parent)
        self.parent = parent
        self.appConfig = appConfig
        self.maxChapter = appConfig["maximumChapter"]

        selectColor = appConfig.get("colors", {}).get("selectBackground", "#00c5ff")
        self.listbox = Listbox(
            self,
            selectmode="single",
            height=3,
            selectbackground=selectColor,
            width=40,
            exportselection=False,
        )
        self.listbox.pack(fill="both", expand=True)
        self.currentChapter = appConfig["defaultChapter"]
        self.activeSavesData = getActiveDisplayData(self.currentChapter, self.appConfig)
        self.fill_list(self.activeSavesData["strings"])

    def updateToChapter(self, chapter: int):
        self.currentChapter = chapter
        self.activeSavesData = getActiveDisplayData(self.currentChapter, self.appConfig)
        self.fill_list(self.activeSavesData["strings"])

    def fill_list(self, saves):
        self.listbox.delete(0, "end")
        for i, save in enumerate(saves):
            self.listbox.insert("end", save)

    def listBoxUpdateCommand(self):
        currentChapter = self.currentChapter
        # Set to default chapter if out of range, currently raises an error.
        if currentChapter < 1 or currentChapter > self.maxChapter:
            raise ValueError(f"Chapter must be between 1 and {self.maxChapter}.")

        self.activeSavesData = getActiveDisplayData(currentChapter, self.appConfig)
        self.fill_list(self.activeSavesData["strings"])

    def getSelectedSaveSlot(self):
        selected = self.listbox.curselection()
        if selected == ():
            return -1
        if self.activeSavesData["slotData"][selected[0]]["exists"] is False:
            return {
                "exists": False,
                "chapter": self.currentChapter,
                "slot": selected[0],
            }

        return {
            "exists": True,
            "chapter": self.currentChapter,
            "slot": selected[0],
            "isComplete": self.activeSavesData["slotData"][int(selected[0])][
                "isComplete"
            ],
        }


class BackupFrame(Frame):
    def __init__(
        self,
        parent,
        appConfig: dict,
        newFolderEnabled: bool = False,
        hideSaves: bool = False,
    ):
        super().__init__(parent)
        self.parent = parent
        self.maxChapter = appConfig["maximumChapter"]
        self.hideSaves = hideSaves

        self.displayPath = StringVar(self)
        self.displayEntry = Entry(
            self, textvariable=self.displayPath, width=40, exportselection=False
        )
        self.displayEntry.config(state=DISABLED)
        selectColor = appConfig.get("colors", {}).get("selectBackground", "#00c5ff")
        self.backupListbox = ScrollableListbox(self, selectColor)
        # Bind a command to selecting an item in the listbox
        self.backupListbox.bind_listbox(
            "<<ListboxSelect>>", lambda _: self.listBoxSelectCommand()
        )
        # Bind double click to open the folder
        self.backupListbox.bind("<Double-Button-1>", lambda _: self.openFolder())
        self.displayEntry.pack(side=TOP, anchor=NW)
        self.backupListbox.pack(side=TOP, anchor=NW)

        self.buttonBox = Frame(self)
        self.navigateDirectoryDown = Button(
            self.buttonBox, text="Open", command=self.openFolder, state=DISABLED
        )
        self.navigateDirectoryDown.pack(side=LEFT)
        self.navigateDirectoryUp = Button(
            self.buttonBox, text="Back", command=self.goBack, state=DISABLED
        )
        self.navigateDirectoryUp.pack(side=LEFT)
        self.newFolderButton = Button(
            self.buttonBox, text="New Folder", command=self.createNewFolder
        )
        # Only show the new folder button if newFolderEnabled is True
        if newFolderEnabled:
            self.newFolderButton.pack(side=LEFT)

        self.buttonBox.pack(side=TOP, anchor=NW)

        self.backupListboxData = []
        self.setChapter(appConfig["defaultChapter"])

    def setChapter(self, chapter):
        if not os.path.exists(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{chapter}")):
            showerror(
                title="Fatal Error",
                message=f"Error, chapter {chapter} backup path does not exist",
            )
        self.displayPath.set(value=f"CH{chapter}:\\")
        self.basePath = os.path.join(os.environ["DSM_BKP_PATH"], f"CH{chapter}")
        self.currentPath = self.basePath
        self.populateListbox()

    def populateListbox(self):
        # Clear Listbox
        self.backupListbox.delete(0, "end")
        self.backupListboxData = []

        # Get all folders in the directory
        for dir in os.listdir(self.currentPath):
            if os.path.isdir(os.path.join(self.currentPath, dir)):
                self.backupListboxData.append(("dir", dir))
                self.backupListbox.insert("end", f"[Folder] {dir}")
        # Populate the listbox with backup files
        for file in os.listdir(self.currentPath):
            if file.endswith(".drsave") and not self.hideSaves:
                self.backupListboxData.append(("file", file))
                self.backupListbox.insert(
                    "end", f"[Save] {file.replace('.drsave', '')}"
                )

    def openFolder(self):
        # Get the selected item from the listbox
        selected = self.backupListbox.curselection()
        if not selected:
            return
        # Check if the selected item is a folder
        selectedItem = self.backupListboxData[selected[0]]
        if selectedItem[0] != "dir":
            return
        # Get the path of the selected folder
        folderPath = os.path.join(self.currentPath, selectedItem[1])
        if not os.path.exists(folderPath):
            return showerror(
                title="Error", message=f"Folder {selectedItem[1]} does not exist."
            )
        # Update the current path and display it
        self.currentPath = folderPath
        self.displayPath.set(value=self.displayPath.get() + selectedItem[1] + "\\")
        self.populateListbox()

        # Set the back button to enabled
        self.navigateDirectoryUp.config(state=NORMAL)

    def goBack(self):
        # Check if we are already at the base path
        if self.currentPath == self.basePath:
            return
        # Get the parent directory of the current path
        parentPath = os.path.dirname(self.currentPath)
        if not os.path.exists(parentPath):
            return showerror(
                title="Error", message=f"Parent directory {parentPath} does not exist."
            )
        # Update the current path and display it
        self.currentPath = parentPath
        # Update the display path to remove the last folder
        newDisplayPath = self.displayPath.get().split("\\")[
            :-2
        ]  # Remove the last folder and the trailing slash
        # Set the display path to the new path
        self.displayPath.set("\\".join(newDisplayPath) + "\\")
        # Repopulate the listbox
        self.populateListbox()
        # If we are back at the base path, disable the back button
        if self.currentPath == self.basePath:
            self.navigateDirectoryUp.config(state=DISABLED)
        self.navigateDirectoryDown.config(state=DISABLED)

    def createNewFolder(self):
        # Get the name of the new folder from the user

        newFolderName = askstring("New Folder", "Enter the name of the new folder:")
        if newFolderName is None:
            return
        # Check if the string contains invalid filename characters
        invalidChars = r'\/:*?"<>|'
        if any(char in newFolderName for char in invalidChars):
            return showerror(
                title="Error",
                message=f"Folder name cannot contain any of the following characters: {invalidChars}",
            )
        # Check if the folder name is empty or consists only of whitespace
        if newFolderName.strip() == "":
            return showerror(title="Error", message="Folder name cannot be empty.")
        # Check if the folder name is already taken
        newFolderName = newFolderName.strip()  # Remove leading and trailing whitespace
        if newFolderName in [item[1] for item in self.backupListboxData]:
            return showerror(
                title="Error", message=f"Folder {newFolderName} already exists."
            )

        # Create the new folder in the current path
        newFolderPath = os.path.join(self.currentPath, newFolderName)
        try:
            os.mkdir(newFolderPath)
        except FileExistsError:
            return showerror(
                title="Error", message=f"Folder {newFolderName} already exists."
            )
        except Exception as e:
            return showerror(
                title="Error", message=f"Failed to create folder: {str(e)}"
            )

        # Repopulate the listbox to include the new folder
        self.populateListbox()

    def listBoxSelectCommand(self):
        # Get the selected item from the listbox
        selected = self.backupListbox.curselection()
        if not selected:
            return
        # Check if the selected item is a folder
        selectedItem = self.backupListboxData[selected[0]]
        if selectedItem[0] != "dir":
            # Disable the open button if the selected item is not a folder
            self.navigateDirectoryDown.config(state=DISABLED)
            return
        # Enable the open button if the selected item is a folder
        self.navigateDirectoryDown.config(state=NORMAL)

    def getSelectedSave(self):
        selected = self.backupListbox.curselection()
        if selected == ():
            return -1
        if self.backupListboxData[selected[0]][0] == "dir":
            return -1
        return {
            "selectedIndex": selected[0],
            "selectedName": self.backupListboxData[selected[0]][1],
            "selectedPath": os.path.join(
                self.currentPath, self.backupListboxData[selected[0]][1]
            ),
        }

    def getSelectedFolder(self):
        selected = self.backupListbox.curselection()
        if selected == ():
            return -1
        if self.backupListboxData[selected[0]][0] != "dir":
            return -1
        return {
            "selectedIndex": selected[0],
            "selectedName": self.backupListboxData[selected[0]][1],
            "selectedPath": os.path.join(
                self.currentPath, self.backupListboxData[selected[0]][1]
            ),
        }


class RightButtonBox(LabelFrame):
    def __init__(
        self,
        parent,
        backup_command: Callable,
        restore_command: Callable,
        settings_command: Callable,
        launch_command: Callable,
        delete_save_command: Callable,
        edit_save_command: Callable,
        download_example_saves_command: Callable,
        exit_command: Callable,
    ):
        super().__init__(parent)
        self.parent = parent
        self.config(text="Options")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.button1 = Button(self, text="Backup Save", command=backup_command)
        self.button1.grid(row=0, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button2 = Button(self, text="Restore Save", command=restore_command)
        self.button2.grid(row=1, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button3 = Button(self, text="Delete Save", command=delete_save_command)
        self.button3.grid(row=2, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button4 = Button(self, text="Settings", command=settings_command)
        self.button4.grid(row=3, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button5 = Button(self, text="Launch Game", command=launch_command)
        self.button5.grid(row=4, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button6 = Button(self, text="Edit Active Save", command=edit_save_command)
        self.button6.grid(row=5, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.button8 = Button(
            self,
            text="Download Example Saves",
            command=download_example_saves_command,
            state=DISABLED,
        )
        self.button8.grid(row=6, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)
        self.buttonExit = Button(self, text="Exit", command=exit_command)
        self.buttonExit.grid(row=7, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)

        # self.buttonTest = Button(self, text="Test", command=test_command)
        # self.buttonTest.grid(row=8, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)


class ScrollableListbox(Frame):
    def __init__(
        self, parent, selectbackground, items=None, height=10, width=40, **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.listbox = Listbox(
            self, height=height, width=width, selectbackground=selectbackground
        )
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=LEFT, fill="both", expand=True)
        self.scrollbar.pack(side=RIGHT, fill="y")
        if items:
            for item in items:
                self.listbox.insert("end", item)

    def insert(self, index, item):
        self.listbox.insert(index, item)

    def delete(self, first, last=None):
        self.listbox.delete(first, last)

    def get(self, first, last=None):
        return self.listbox.get(first, last)

    def curselection(self):
        return self.listbox.curselection()

    def bind_listbox(self, sequence=None, func=None, add=None):
        self.listbox.bind(sequence, func, add)


class TempFrame(LabelFrame):
    def __init__(self, parent, button_command1: Callable, button_command2: Callable):
        super().__init__(parent)
        self.parent = parent
        self.config(text="Temporary Frame")

        self.button1 = Button(self, text="Button 1", command=button_command1)
        self.button1.pack(side=LEFT, padx=5, pady=5)
        self.button2 = Button(self, text="Button 2", command=button_command2)
        self.button2.pack(side=LEFT, padx=5, pady=5)


def createCutPath(path: str, entryWidth: int):
    """
    Creates a shortened version of the path for display purposes.
    If the path is longer than entryWidth, it will be cut and prefixed with '...'.
    """
    if len(path) > entryWidth:
        return "..." + path[-(entryWidth - 3) :]
    return path


def openFolderPicker(title: str, initialDir: str, entryWidth: int):
    directory = askdirectory(title=title, initialdir=initialDir)
    if not directory:
        return

    return [directory, createCutPath(directory, entryWidth)]


def openFilePicker(title: str, initialDir: str, entryWidth: int, filetypes=None):
    from tkinter.filedialog import askopenfilename

    file = askopenfilename(title=title, initialdir=initialDir, filetypes=filetypes)
    if not file:
        return

    return [file, createCutPath(file, entryWidth)]


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
