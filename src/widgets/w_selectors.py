from tkinter import (
    Button,
    Checkbutton,
    Entry,
    Frame,
    IntVar,
    LabelFrame,
    Radiobutton,
    StringVar,
)
from tkinter.constants import DISABLED, NORMAL, W

from src.utils import createCutPath, openFilePicker, openFolderPicker


class PathSelectorFrame(LabelFrame):
    def __init__(
        self,
        parent,
        *,
        initialDir: str,
        picker,
        pickerTitle: str,
        entryWidth: int = 40,
        picker_kwargs=None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.initialDir = initialDir
        self.entryWidth = entryWidth

        # Function used to open the picker
        self._picker = picker
        self._pickerTitle = pickerTitle
        self._picker_kwargs = picker_kwargs or {}

        self.selectedPath = ""

        self.pathDisplay = StringVar(value="[Nothing Selected]")

        self.entryFrame = Frame(self)

        self.pathEntry = Entry(
            self.entryFrame,
            width=self.entryWidth,
            textvariable=self.pathDisplay,
            state=DISABLED,
        )

        self.selectButton = Button(
            self.entryFrame,
            text="Select",
            command=self.selectPath,
        )

        self.pathEntry.grid(column=0, row=0, padx=(5, 2.5), pady=(0, 5))
        self.selectButton.grid(column=1, row=0, padx=(2.5, 5), pady=(0, 5))

        self.entryFrame.pack()

    def selectPath(self):
        result = self._picker(
            self._pickerTitle,
            initialDir=self.initialDir,
            entryWidth=self.entryWidth,
            **self._picker_kwargs,
        )

        if not result:
            return

        self.selectedPath = result[0]
        self.pathDisplay.set(result[1])

    def getPath(self):
        return self.selectedPath

    def setPath(self, value: str):
        if not value:
            return

        self.selectedPath = value
        self.pathDisplay.set(createCutPath(value, self.entryWidth))

    def enableSelection(self):
        self.selectButton.config(state=NORMAL)

    def disableSelection(self):
        self.selectButton.config(state=DISABLED)


class RadioPathSelectorFrame(PathSelectorFrame):
    def __init__(
        self,
        parent,
        *,
        initialDir,
        picker,
        pickerTitle,
        defaultText,
        customText,
        defaultType,
        entryWidth=40,
        picker_kwargs=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            initialDir=initialDir,
            picker=picker,
            pickerTitle=pickerTitle,
            entryWidth=entryWidth,
            picker_kwargs=picker_kwargs,
            **kwargs,
        )

        self.defaultType = defaultType

        self.selectedOption = IntVar()

        self.defaultRadio = Radiobutton(
            self,
            text=defaultText,
            variable=self.selectedOption,
            value=1,
            command=self.sel,
        )

        self.customRadio = Radiobutton(
            self,
            text=customText,
            variable=self.selectedOption,
            value=2,
            command=self.sel,
        )

        self.defaultRadio.pack(anchor=W)
        self.customRadio.pack(anchor=W)

        # Move the inherited entry frame underneath the radio buttons
        self.entryFrame.pack_forget()
        self.entryFrame.pack()

        self.defaultRadio.invoke()

    def sel(self):
        if self.selectedOption.get() == 1:
            self.disableSelection()
        else:
            self.enableSelection()

    def getValue(self):
        if self.selectedOption.get() == 1:
            return {"type": self.defaultType}

        return {
            "type": "custom",
            "path": self.getPath(),
        }

    def setValue(self, value):
        if not value:
            return

        if value["type"] == self.defaultType:
            self.defaultRadio.invoke()
        elif value["type"] == "custom":
            self.customRadio.invoke()
            self.setPath(value["path"])


class BackupSaveLocationSelectorFrame(PathSelectorFrame):
    def __init__(self, parent, initialDir, **kwargs):
        super().__init__(
            parent,
            initialDir=initialDir,
            picker=openFolderPicker,
            pickerTitle="Select the backup save location:",
            text="Backup Save Location",
            **kwargs,
        )

    def getValue(self):
        return self.getPath()

    def setValue(self, value):
        self.setPath(value)


class ActiveSaveLocationSelectorFrame(RadioPathSelectorFrame):
    def __init__(self, parent, initialDir, **kwargs):
        super().__init__(
            parent,
            initialDir=initialDir,
            picker=openFolderPicker,
            pickerTitle="Select the custom active save location:",
            defaultText="Default (%localappdata%\\DELTARUNE)",
            customText="Custom Location",
            defaultType="default",
            text="Active Save Location",
            **kwargs,
        )


class GameSelectSelectorFrame(RadioPathSelectorFrame):
    def __init__(self, parent, initialDir, **kwargs):
        super().__init__(
            parent,
            initialDir=initialDir,
            picker=openFilePicker,
            pickerTitle="Select the custom game executable:",
            defaultText="Use Steam Link",
            customText="Custom Location",
            defaultType="steam",
            picker_kwargs={
                "filetypes": [
                    ("Executable Files", "*.exe"),
                    ("All Files", "*.*"),
                ]
            },
            text="Game Launch",
            **kwargs,
        )

        self.run_game_follows_active_chapter = IntVar(value=0)

        self.run_game_check = Checkbutton(
            self,
            text="Run Game Follows Active Chapter",
            variable=self.run_game_follows_active_chapter,
        )

        self.run_game_check.pack(anchor=W)

    def setFollowActiveChapter(self, value: bool):
        self.run_game_follows_active_chapter.set(int(value))

    def getFollowActiveChapter(self) -> bool:
        return bool(self.run_game_follows_active_chapter.get())
