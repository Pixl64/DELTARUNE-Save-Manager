import json
import os
from tkinter import LabelFrame, Tk
from tkinter.constants import BOTH, LEFT, NW, TOP, Y
from tkinter.messagebox import (
    askyesno,
    askyesnocancel,
    showerror,
    showinfo,
    showwarning,
)
from typing import Any

from src.config_load import loadAppConfig, loadUserConfig
from src.file_utils import launch_game, setUpDirectories
from src.gui_utils import set_window_middle, setWindowIcon
from src.popup.backup_create import BackupCreatePopup
from src.popup.game_select import GameSelectPopup
from src.popup.settings import SettingsPopup
from src.save_backup_restore import backupSave, restoreSave
from src.save_editor.saveedit import SaveFileEdit
from src.widgets.w_active_frame import ActiveFrame
from src.widgets.w_backup_frame import BackupFrame
from src.widgets.w_buttonbox import RightButtonBox
from src.widgets.w_chapter_frame import ChapterSelectFrame


class App(Tk):
    def __init__(self, userConfig: dict[str, Any], appConfig: dict[str, Any]) -> None:
        super().__init__()
        self.withdraw()  # Hide the main window until everything is set up
        self.title("DELTARUNE Save Manager")

        setWindowIcon(self)  # Set the window icon

        self.size = (455, 325)
        self.resizable(False, False)

        self.userConfig = userConfig
        self.appConfig = appConfig

        set_window_middle(
            self, self.size[0], self.size[1]
        )  # Set the window to the middle of the screen
        self.protocol(
            "WM_DELETE_WINDOW", self.exit
        )  # Set the close button to call the exit method

        self.place_widgets()
        self.deiconify()

    def place_widgets(self) -> None:
        self.saveInfoFrame = LabelFrame(
            self, text="Save Information", width=300, height=400
        )
        self.activeSaves = ActiveFrame(self.saveInfoFrame, self.appConfig)
        self.chapterSelectFrame = ChapterSelectFrame(
            self.saveInfoFrame, self.appConfig, listBoxUpdateCommand=self.chapterChange
        )
        self.backupSaves = BackupFrame(self.saveInfoFrame, self.appConfig)

        self.chapterSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=(5, 0))
        self.activeSaves.pack(side=TOP, anchor=NW, padx=5)
        self.backupSaves.pack(side=TOP, anchor=NW, padx=5, pady=5)

        self.buttonBox = RightButtonBox(
            self,
            self.userConfig,
            self.appConfig,
            backup_command=self.backupSaveCommand,
            restore_command=self.restoreSaveCommand,
            settings_command=self.showSettings,
            launch_command=self.ui_launchGame,
            delete_save_command=self.deleteSave,
            edit_save_command=self.editSave,
            download_example_saves_command=lambda: showinfo(
                title="Info", message="This feature is not yet implemented."
            ),
            exit_command=self.exit,
        )

        self.saveInfoFrame.pack(side=LEFT, anchor=NW, padx=5, pady=5, fill=Y)
        self.buttonBox.pack(
            side=LEFT, anchor=NW, padx=5, pady=5, fill=BOTH, expand=True
        )

    def chapterChange(self, chapter: int) -> None:
        self.activeSaves.updateToChapter(chapter)
        self.backupSaves.setChapter(chapter)
        self.buttonBox.setChapter(chapter)

    def backupSaveCommand(self) -> None:
        # Get the currently selected chapter
        currentSave = self.activeSaves.getSelectedSaveSlot()

        if currentSave == -1:
            showerror(title="Error", message="Please select a slot to backup.")
            return
        if not currentSave["exists"]:
            showerror(title="Error", message="Selected slot does not exist.")
            return
        if currentSave["isComplete"]:
            backUpComplete = askyesnocancel(
                title="Backup Complete Save",
                message="You are about to backup a save with a Completion File. Do you want to include the Completion File in the backup?",
            )
            if backUpComplete is None:
                return
            currentSave["useComplitionData"] = backUpComplete
        else:
            currentSave["useComplitionData"] = False

        # Bring up new save popup
        newSavePopup = BackupCreatePopup(
            self,
            currentSave["chapter"],
            self.appConfig,
            title="Where",
            saveDir=os.path.join(
                os.environ["DSM_BKP_PATH"], f"CH{currentSave['chapter']}"
            ),
        )
        if newSavePopup.result is None:
            return

        backupSave(
            currentSave["chapter"],
            currentSave["slot"],
            newSavePopup.result["saveLocation"],
            useComplete=currentSave["useComplitionData"],
        )

        self.chapterChange(
            currentSave["chapter"]
        )  # Update all frames to the current chapter

        showinfo(
            title="Backup Complete",
            message=f"Backup of Chapter {currentSave['chapter']} Slot {currentSave['slot'] + 1} created successfully!",
        )

    def restoreSaveCommand(self) -> None:
        # Get currently selected backup save
        currentBackup = self.backupSaves.getSelectedSave()
        # Get currently selected save slot and chapter
        currentSave = self.activeSaves.getSelectedSaveSlot()

        # Check if a backup save is selected
        if currentBackup == -1:
            showerror(title="Error", message="Please select a backup save to restore.")
            return
        # Check if a save slot is selected
        if currentSave == -1:
            showerror(title="Error", message="Please select a slot to restore to.")
            return

        if currentSave["exists"]:
            backUpExisting = askyesnocancel(
                title="Overwrite Save",
                message=f"A save file already exists in Chapter {currentSave['chapter']} Slot {currentSave['slot'] + 1}. Would you like to back it up before restoring the backup save?",
            )
            if backUpExisting is None:
                return
            if backUpExisting:
                # Backup the existing save
                backupCreatePopup = BackupCreatePopup(
                    self,
                    currentSave["chapter"],
                    self.appConfig,
                    title="Where",
                    saveDir=os.path.join(
                        os.environ["DSM_BKP_PATH"], f"CH{currentSave['chapter']}"
                    ),
                )
                if backupCreatePopup.result is None:
                    return
                backupSave(
                    currentSave["chapter"],
                    currentSave["slot"],
                    backupCreatePopup.result["saveLocation"],
                    useComplete=currentSave["useComplitionData"],
                )

        # Restore the backup save
        restoreSave(
            currentBackup["selectedPath"], currentSave["chapter"], currentSave["slot"]
        )

        self.chapterChange(
            currentSave["chapter"]
        )  # Update all frames to the current chapter

        showinfo(
            title="Restore Complete",
            message=f"Backup '{currentBackup['selectedName'].replace('.drsave', '')}' restored to Chapter {currentSave['chapter']} Slot {currentSave['slot'] + 1} successfully!",
        )

    def showSettings(self) -> None:
        settingsPopup = SettingsPopup(
            self,
            self.appConfig["appID"],
            title="Settings",
            initialDir=os.environ["DSM_PATH"],
        )
        if not settingsPopup.result:
            return

        # Save the settings to user_config.json
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(settingsPopup.result, f, indent=4)

        # Get current chapter from the active saves
        currentChapter = self.activeSaves.currentChapter
        # Reload Configs
        self.appConfig = loadAppConfig()
        self.userConfig = loadUserConfig()
        setUpDirectories(self.appConfig)
        self.chapterChange(currentChapter)  # Update the chapter select frame
        self.buttonBox.updateConfig(self.userConfig)

    def ui_launchGame(
        self,
    ) -> None:
        if os.environ["DR_EXE_PATH"] == "NOT_SET":
            popup = GameSelectPopup(self)
            if not popup.result:
                return

            # Save the path to user_config.json
            userConfig = loadUserConfig()
            userConfig["launchData"] = popup.result["launchData"]
            userConfig["runGameFollowsActiveChapter"] = popup.result.get(
                "runGameFollowsActiveChapter", False
            )
            with open(
                os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w"
            ) as f:
                json.dump(userConfig, f, indent=4)
            # Reload the userConfig from the file to ensure it is up to date
            self.userConfig = loadUserConfig()

        launch_game(self.appConfig, self.userConfig, self.buttonBox.getChapter())

        self.buttonBox.updateConfig(
            self.userConfig
        )  # Update the button box with the new config after launching the game

    def editSave(self) -> None:
        # Get currently selected save slot and chapter
        currentSave = self.activeSaves.getSelectedSaveSlot()

        # Checks
        if currentSave == -1:
            showerror(title="Error", message="Please select a save to edit.")
            return
        if not currentSave["exists"]:
            showerror(title="Error", message="Selected save does not exist.")
            return

        if not self.userConfig.get("hasSeenEditWarning", False):
            showwarning(
                title="Warning",
                message="Editing save data can potentially break a save file. Please back up your save before continuing.",
            )
            self.userConfig["hasSeenEditWarning"] = True
            with open(
                os.path.join(os.environ["DSM_PATH"], "user_config.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(self.userConfig, f, indent=4)

        SaveFileEdit(
            self,
            currentSave["chapter"],
            currentSave["slot"],
            self.appConfig["dw_invItems"],
            self.appConfig[f"chapter{currentSave['chapter']}"],
            self.appConfig,
            title=f"Editing save from Ch{currentSave['chapter']} slot {currentSave['slot'] + 1}",
        )

    def deleteSave(self) -> None:
        # Get currently selected backup save
        currentBackup = self.backupSaves.getSelectedSave()
        # Get currently selected save slot and chapter
        currentSave = self.activeSaves.getSelectedSaveSlot()

        # Check if they are both -1
        if currentBackup == -1 and currentSave == -1:
            showerror(title="Error", message="Please select a save to delete.")
            return

        # Check if both are selected
        if currentBackup != -1 and currentSave != -1:
            showerror(
                title="Error",
                message="Please select either a backup save or an active save to delete, not both.",
            )
            self.chapterChange(
                self.chapterSelectFrame.getChapter()
            )  # Update all frames to the current chapter
            return

        if currentBackup != -1:
            # Delete the selected backup save
            confirmDelete = askyesno(
                title="Delete Backup Save",
                message=f"Are you sure you want to delete the backup save '{currentBackup['selectedName']}'?",
            )
            if confirmDelete is None:
                return
            if confirmDelete:
                os.remove(currentBackup["selectedPath"])
                self.chapterChange(
                    self.chapterSelectFrame.getChapter()
                )  # Update all frames to the current chapter
            return

        if currentSave != -1:
            # Delete the active save
            confirmDelete = askyesno(
                title="Delete Active Save",
                message=f"Are you sure you want to delete the active save in Chapter {currentSave['chapter']} Slot {currentSave['slot'] + 1}?",
            )
            if confirmDelete is None:
                return
            if confirmDelete:
                if os.environ["DR_EXE_PATH"] in ["VIA_STEAM", "NOT_SET"]:
                    confirmSteamOpen = askyesno(
                        title="Steam Cloud Check",
                        message="If you are using Steam and have Steam Cloud enabled, it will automatically restore the save. However if you have the game open on the chapter select screen it will not restore the save. \nDo you want to open the game to ensure the save is deleted?",
                    )
                    if confirmSteamOpen is None:
                        return
                    if confirmSteamOpen:
                        self.ui_launchGame()
                        showinfo(
                            title="Opening Game",
                            message="Opening the game to ensure the save is deleted. Please Press OK to continue when the game is open.",
                        )
                # Delete the save file
                savePath = os.path.join(
                    os.environ["DR_SAVE_PATH"],
                    f"filech{currentSave['chapter']}_{currentSave['slot']}",
                )
                if os.path.exists(savePath):
                    os.remove(savePath)

            self.chapterChange(
                self.chapterSelectFrame.getChapter()
            )  # Update all frames to the current chapter
            return

    def exit(self) -> None:
        print("Exiting app...")
        self.destroy()
        self.quit()
