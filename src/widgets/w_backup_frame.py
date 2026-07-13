import os
from tkinter import (
    DISABLED,
    NORMAL,
    TOP,
    Button,
    Entry,
    Frame,
    StringVar,
)
from tkinter.constants import LEFT, NW
from tkinter.messagebox import showerror
from tkinter.simpledialog import askstring

from src.widgets.w_general import ScrollableListbox


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
