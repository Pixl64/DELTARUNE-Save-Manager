import os
import subprocess
from collections.abc import Callable
from tkinter import Button, Frame, Label, LabelFrame, Spinbox, StringVar
from tkinter.constants import DISABLED, EW, LEFT, NW, RIGHT, X
from tkinter.messagebox import showerror, showinfo

from src.file_utils import (
    get_deltarune_location,
    link_music_to_chapters,
    remove_music_links,
)


class RightButtonBox(LabelFrame):
    def __init__(
        self,
        parent,
        userConfig: dict,
        appConfig: dict,
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

        self.appConfig = appConfig
        self.chapter = 1

        self.chapter_limits = (0, appConfig["maximumChapter"])  # (min, max)
        self.runGameFollowsActiveChapter = userConfig.get(
            "runGameFollowsActiveChapter", False
        )

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

        self.launch_chapter_value_sv = StringVar(value="1")

        self.launch_chapter_value_sv.trace_add(
            "write",
            lambda *args: self._update_chapter(int(self.launch_chapter_value_sv.get())),
        )

        self.chapter_launch_frame = Frame(self)
        self.button5 = Button(
            self.chapter_launch_frame, text="Launch Game", command=launch_command
        )
        self.button5.pack(side=LEFT, fill=X, expand=True)

        self.chapter_spinbox = Spinbox(
            self.chapter_launch_frame,
            from_=0,
            to=self.chapter_limits[1],
            width=1,
            wrap=True,
            textvariable=self.launch_chapter_value_sv,
            state="readonly",
        )
        self.chapter_spinbox.pack(side=RIGHT, padx=1, ipady=4, ipadx=2)

        self.chapter_launch_frame.grid(
            row=4, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2
        )

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

        # Set the initial chapter based on the userConfig
        self.updateConfig(userConfig)

        # self.buttonTest = Button(self, text="Test", command=test_command)
        # self.buttonTest.grid(row=8, column=0, padx=5, pady=2.5, sticky=EW, columnspan=2)

    def updateSpinboxState(self):
        if self.runGameFollowsActiveChapter:
            self.chapter_spinbox.config(state="disabled")
        else:
            self.chapter_spinbox.config(state="readonly")

    def _update_chapter(self, chapter: int) -> None:
        if chapter < self.chapter_limits[0]:
            chapter = self.chapter_limits[0]
        elif chapter > self.chapter_limits[1]:
            chapter = self.chapter_limits[1]

        if chapter == 0:
            self.button5.config(text="Launch Game")
        else:
            self.button5.config(text="Launch Chapter: ")

        self.launch_chapter_value_sv.set(str(chapter))
        self.chapter = chapter

    def updateConfig(self, userConfig: dict):
        self.runGameFollowsActiveChapter = userConfig.get(
            "runGameFollowsActiveChapter", False
        )

        self.updateSpinboxState()

        if self.runGameFollowsActiveChapter:
            self._update_chapter(self.chapter)
        else:
            self._update_chapter(0)

    def getChapter(self) -> int:
        return self.chapter

    def setChapter(self, chapter: int) -> None:
        if self.runGameFollowsActiveChapter:
            self._update_chapter(chapter)


class OpenFolderButtonBox(LabelFrame):
    def __init__(self, parent, appID: int):
        super().__init__(parent)
        self.parent = parent
        self.config(text="Open Folder")

        self.grid_columnconfigure(0, weight=1, uniform="buttons")
        self.grid_columnconfigure(1, weight=1, uniform="buttons")

        self.activeSaveButton = Button(
            self, text="Open Active Save Folder", command=self.open_active_save_folder
        )

        self.exeLocationButton = Button(
            self,
            text="Open Game Location",
            command=lambda: self.open_game_exe_location(appID),
        )

        self.backupSaveButton = Button(
            self, text="Open Backup Save Folder", command=self.open_backup_save_folder
        )

        self.activeSaveButton.grid(row=0, column=0, padx=5, pady=2.5, sticky=EW)
        self.exeLocationButton.grid(row=0, column=1, padx=5, pady=2.5, sticky=EW)
        self.backupSaveButton.grid(row=1, column=0, padx=5, pady=2.5, sticky=EW)

    def open_active_save_folder(self):
        activeSaveData = os.environ.get("DR_SAVE_PATH", None)
        if activeSaveData is None:
            showerror(
                title="Error",
                message="Active Save Location is not set. Please set it in the settings.",
            )
            return

        if os.path.exists(activeSaveData):
            subprocess.Popen(f'explorer "{activeSaveData}"')
        else:
            showerror(
                title="Error",
                message=f"Active Save Location does not exist.\n{activeSaveData}",
            )

    def open_backup_save_folder(self):
        backupSaveData = os.environ.get("DSM_BKP_PATH", None)

        if backupSaveData is None:
            showerror(
                title="Error",
                message="Backup Save Location is not set. Please set it in the settings.",
            )
            return

        if os.path.exists(backupSaveData):
            os.startfile(backupSaveData)
        else:
            showerror(
                title="Error",
                message=f"Backup Save Location does not exist.\n{backupSaveData}",
            )

    def open_game_exe_location(self, appID: int):
        gamePath = os.environ.get("DR_EXE_PATH", None)
        if gamePath is None or "NOT_SET" in gamePath:
            showerror(
                title="Error",
                message="Game Executable Location is not set. Please set it in the settings.",
            )
            return

        gamePath = get_deltarune_location(appID)

        if os.path.exists(gamePath):
            if gamePath.endswith(".exe"):
                os.startfile(os.path.dirname(gamePath))
            else:
                os.startfile(gamePath)
        else:
            showerror(
                title="Error",
                message=f"Game Executable Location does not exist.\n{gamePath}",
            )


class ChapterLaunchPatch(LabelFrame):
    def __init__(self, parent, appID):
        super().__init__(parent)
        self.parent = parent
        self.config(text="Chapter Launch Patch")
        self.appID = appID
        self.grid_columnconfigure(0, weight=1)

        self.patchDescriptionLabel = Label(
            self,
            text="Patch the /mus files to allow launching chapters directly. Only required if you are using the Steam version of DELTARUNE.",
            wraplength=300,
            justify=LEFT,
        )
        self.patchDescriptionLabel.grid(
            row=0, column=0, padx=5, pady=2.5, sticky=NW, columnspan=2
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.patchButton = Button(
            self, text="Patch /mus files", command=self.patch_command
        )
        self.patchButton.grid(row=1, column=0, padx=5, pady=2.5, sticky=EW)

        self.unPatchButton = Button(
            self, text="Unpatch /mus files", command=self.unpatch_command
        )
        self.unPatchButton.grid(row=1, column=1, padx=5, pady=2.5, sticky=EW)

    def patch_command(self):
        try:
            res = link_music_to_chapters(get_deltarune_location(self.appID))
        except FileNotFoundError as e:
            showerror(
                title="Patch Error",
                message=f"An error occurred while patching the /mus files:\n{e!s}",
            )
            return
        showinfo(
            title="Patch Result",
            message=res,
        )

    def unpatch_command(self):
        try:
            res = remove_music_links(get_deltarune_location(self.appID))
        except FileNotFoundError as e:
            showerror(
                title="Patch Error",
                message=f"An error occurred while patching the /mus files:\n{e!s}",
            )
            return
        showinfo(
            title="Patch Result",
            message=res,
        )
