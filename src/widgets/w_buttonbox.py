import os
import subprocess
from tkinter import Button, LabelFrame
from tkinter.constants import DISABLED, EW
from tkinter.messagebox import showerror
from typing import Callable


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


class OpenFolderButtonBox(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config(text="Open Folder")

        self.grid_columnconfigure(0, weight=1, uniform="buttons")
        self.grid_columnconfigure(1, weight=1, uniform="buttons")

        self.activeSaveButton = Button(
            self, text="Open Active Save Folder", command=self.open_active_save_folder
        )

        self.exeLocationButton = Button(
            self, text="Open Game Location", command=self.open_game_exe_location
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

    def open_game_exe_location(self):
        gamePath = os.environ.get("DR_EXE_PATH", None)
        if gamePath is None or "NOT_SET" in gamePath:
            showerror(
                title="Error",
                message="Game Executable Location is not set. Please set it in the settings.",
            )
            return

        if gamePath == "VIA_STEAM":
            steamPath = self.get_steam_install_location()
            if steamPath is None:
                showerror(
                    title="Error",
                    message="Steam installation location could not be found. Please set the Game Executable Location in the settings.",
                )
                return
            gamePath = os.path.join(steamPath, "steamapps", "common", "DELTARUNE")

        if os.path.exists(gamePath):
            os.startfile(gamePath)
        else:
            showerror(
                title="Error",
                message=f"Game Executable Location does not exist.\n{gamePath}",
            )

    def get_steam_install_location(self):
        try:
            result = subprocess.run(
                ["reg", "query", r"HKCU\Software\Valve\Steam", "/v", "SteamPath"],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.splitlines():
                if "SteamPath" in line:
                    return line.split("REG_SZ")[-1].strip()

        except subprocess.CalledProcessError:
            return None

        return None
