import ctypes
import json
import os
import sys
import tempfile
from typing import Any, Dict

# Get current running directory
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    dataPath = sys._MEIPASS  # type: ignore
    runningDir = os.path.dirname(sys.executable)
    os.chdir(runningDir)
    # Import the pyi_splash module to close the splash screen
    import pyi_splash # type: ignore (This only runs in a pyinstaller environment)
    def killSplash(): pyi_splash.close()
else: 
    runningDir = os.path.dirname(os.path.realpath(__file__))
    dataPath = runningDir
    # Define a dummy function for killSplash if not running as a frozen executable
    def killSplash(): pass

from tkinter import LabelFrame, Tk
from tkinter.constants import BOTH, LEFT, NW, TOP, Y

from tkinter.messagebox import askyesno, askyesnocancel, showerror, showinfo, showwarning

from src.widgets import ActiveFrame, BackupFrame, ChapterSelectFrame, RightButtonBox, setWindowIcon
from src.popup import BackupCreatePopup, FirstTimeSetup, GameSelectPopup, SettingsPopup
from filemanager import backupSave, copyFile, restoreSave
from src.save_editor.saveedit import SaveFileEdit

# Global variables
os.environ["DSM_PATH"] = runningDir
os.environ["DSM_DATA_PATH"] = dataPath

def validateFiles() -> bool:
    """ Validates the existence of the app_config.json and user_config.json files, and creates the user_config.json if it does not exist. """
    # Check for userconfig
    if not os.path.exists(os.path.join(os.environ["DSM_PATH"], "user_config.json")):
        tempW = Tk()
        tempW.withdraw()
        killSplash()
        print("Running first time setup...")
        data = FirstTimeSetup(tempW, title="Select Directory", initialDir=runningDir)
        if not data.result:
            return False
        tempW.destroy()
        with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
            json.dump(data.result, f, indent=4)
        
    return True

def loadJsonConfig(fileName: str) -> Dict[str, Any]:
    """Loads a JSON config from the local directory or embedded data directory."""
    localPath = os.path.join(os.environ["DSM_PATH"], fileName)
    if os.path.exists(localPath):
        with open(localPath) as f:
            return json.load(f)

    print(f"{fileName} not found locally. Using embedded config...")
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        configSrc = os.path.join(os.environ["DSM_DATA_PATH"], fileName)
        configTmp = os.path.join(tempDir, fileName)
        copyFile(configSrc, configTmp)
        with open(configTmp) as f:
            return json.load(f)

def loadAppConfig() -> Dict[str, Any]:
    """Loads the application configuration."""

    config = loadJsonConfig("cfg_app.json")
    chapterConfig = loadJsonConfig("cfg_chapter.json")
    roomNames = loadJsonConfig("cfg_room_names.json")
    inventoryItems = loadJsonConfig("cfg_inventory_items.json")
    
    # Merge default config into chapters
    defaultConfig = chapterConfig.pop("default", {})

    for chapterKey, chapterOverrides in chapterConfig.items():
        mergedConfig = deepMerge(defaultConfig, chapterOverrides)

        # Preserve any existing app-specific values
        if chapterKey in config:
            config[chapterKey] = deepMerge(
                config[chapterKey],
                mergedConfig
            )
        else:
            config[chapterKey] = mergedConfig
    
    for chapterKey, chapterRooms in roomNames.items():
        if chapterKey in config:
            config[chapterKey]["roomNames"] = chapterRooms
    
    config["dw_invItems"] = inventoryItems

    return config

def loadUserConfig() -> Dict[str, Any]:
    """ Loads the user config from user_config.json and sets the environment variables """
    with open(os.path.join(os.environ["DSM_PATH"], "user_config.json")) as f:
        config = json.load(f)
    
    os.environ["DSM_BKP_PATH"] = config["backupSaveLocation"]
    localappdata = os.getenv("LOCALAPPDATA")
    if config["activeSaveLocation"]["type"] == "default":
        os.environ["DR_SAVE_PATH"] = os.path.join(localappdata if localappdata else "", "DELTARUNE")
    else:
        os.environ["DR_SAVE_PATH"] = config["activeSaveLocation"]["path"]
    if "launchData" not in config:
        os.environ["DR_EXE_PATH"] = "NOT_SET"
    else:
        if config["launchData"]["type"] == "steam":
            os.environ["DR_EXE_PATH"] = "VIA_STEAM"
        if config["launchData"]["type"] == "custom":
            os.environ["DR_EXE_PATH"] = config["launchData"]["path"]
    return config

def deepMerge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deepMerge(result[key], value)
        else:
            result[key] = value

    return result

def setUpDirectories(appConfig: Dict[str, Any]) -> None:
    """ Sets up the chapter directories in the backup path """
    for i in range(appConfig["maximumChapter"]):
        if not os.path.exists(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i+1}")):
            os.mkdir(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i+1}"))

class App(Tk):
    def __init__(self, userConfig: Dict[str, Any], appConfig: Dict[str, Any]) -> None:
        super().__init__()
        self.withdraw()  # Hide the main window until everything is set up
        self.title("DELTARUNE Save Manager")
        
        setWindowIcon(self)  # Set the window icon
        
        self.size = (455,325)
        self.resizable(False, False)
        
        self.userConfig = userConfig
        self.appConfig = appConfig
        
        self.set_window_middle(self.size[0], self.size[1]) # Set the window to the middle of the screen
        self.protocol('WM_DELETE_WINDOW', self.exit)  # Set the close button to call the exit method
        
        self.place_widgets()
        self.deiconify()
        
    def place_widgets(self) -> None:
        self.saveInfoFrame = LabelFrame(self, text="Save Information", width=300, height=400)
        self.activeSaves = ActiveFrame(self.saveInfoFrame, self.appConfig)
        self.chapterSelectFrame = ChapterSelectFrame(self.saveInfoFrame, self.appConfig, listBoxUpdateCommand=self.chapterChange)
        self.backupSaves = BackupFrame(self.saveInfoFrame, self.appConfig)
        
        self.chapterSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=(5,0))
        self.activeSaves.pack(side=TOP, anchor=NW, padx=5)
        self.backupSaves.pack(side=TOP, anchor=NW, padx=5, pady=5)
    
        self.buttonBox = RightButtonBox(self,
                                        backup_command=self.backupSaveCommand,
                                        restore_command=self.restoreSaveCommand,
                                        settings_command=self.showSettings,
                                        launch_command=self.launchGame,
                                        delete_save_command=self.deleteSave,
                                        edit_save_command=self.editSave,
                                        exit_command=self.exit                                        
                                    )
        
        self.saveInfoFrame.pack(side=LEFT, anchor=NW, padx=5, pady=5, fill=Y)
        self.buttonBox.pack(side=LEFT, anchor=NW, padx=5, pady=5, fill=BOTH, expand=True)
        
    def set_window_middle(self, width: int, height: int) -> None:
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        middle = screensize[0] // 2, screensize[1] // 2
        add = middle[0] - width // 2, middle[1] - height // 2
        self.geometry(f"{width}x{height}+{add[0]}+{add[1]}")
    
    def chapterChange(self, chapter: int) -> None:
        self.activeSaves.updateToChapter(chapter)
        self.backupSaves.setChapter(chapter)

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
            backUpComplete = askyesnocancel(title="Backup Complete Save", message="You are about to backup a save with a Completion File. Do you want to include the Completion File in the backup?")
            if backUpComplete is None:
                return
            currentSave["useComplitionData"] = backUpComplete
        else:
            currentSave["useComplitionData"] = False
        
        # Bring up new save popup
        newSavePopup = BackupCreatePopup(self, currentSave["chapter"], self.appConfig, title="Where", saveDir=os.path.join(os.environ["DSM_BKP_PATH"], f"CH{currentSave["chapter"]}"))
        if newSavePopup.result is None:
            return
        
        backupSave(currentSave["chapter"], currentSave["slot"], newSavePopup.result["saveLocation"], useComplete=currentSave["useComplitionData"])
        
        self.chapterChange(currentSave["chapter"])  # Update all frames to the current chapter      
        
        showinfo(title="Backup Complete", message=f"Backup of Chapter {currentSave['chapter']} Slot {currentSave['slot']+1} created successfully!")

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
            backUpExisting = askyesnocancel(title="Overwrite Save", message=f"A save file already exists in Chapter {currentSave['chapter']} Slot {currentSave['slot']+1}. Would you like to back it up before restoring the backup save?")
            if backUpExisting is None:
                return
            if backUpExisting:
                # Backup the existing save
                backupCreatePopup = BackupCreatePopup(self, currentSave["chapter"], self.appConfig, title="Where", saveDir=os.path.join(os.environ["DSM_BKP_PATH"], f"CH{currentSave['chapter']}"))
                if backupCreatePopup.result is None:
                    return
                backupSave(currentSave["chapter"], currentSave["slot"], backupCreatePopup.result["saveLocation"], useComplete=currentSave["useComplitionData"])
            
        # Restore the backup save
        restoreSave(currentBackup["selectedPath"], currentSave["chapter"], currentSave["slot"])
        
        self.chapterChange(currentSave["chapter"])  # Update all frames to the current chapter

        showinfo(title="Restore Complete", message=f"Backup '{currentBackup["selectedName"].replace(".drsave", "")}' restored to Chapter {currentSave['chapter']} Slot {currentSave['slot']+1} successfully!")

    def showSettings(self) -> None:
        settingsPopup = SettingsPopup(self, title="Settings", initialDir=os.environ["DSM_PATH"])
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

    def launchGame(self) -> None:
        if os.environ["DR_EXE_PATH"] == "NOT_SET":
            popup = GameSelectPopup(self, title="Select Game", initialDir="C:\\")
            if not popup.result:
                return
            
            # Save the path to user_config.json
            with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "r") as f:
                userConfig = json.load(f)
            userConfig["launchData"] = popup.result["launchData"]
            with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w") as f:
                json.dump(userConfig, f, indent=4)
                
            loadUserConfig()  # Reload user config to update the environment variable
                
        if os.environ["DR_EXE_PATH"] == "VIA_STEAM":
            os.system(f'start steam://rungameid/{self.appConfig["appID"]}')
            return
        if not os.path.exists(os.environ["DR_EXE_PATH"]):
            showerror(title="Error", message="Game executable path does not exist. Please reset it in the settings.")
            return
        else:
            exe_path = os.environ["DR_EXE_PATH"]
            
            # Change running directory to where the deltarune executable is otherwise it won't get past chapter select
            os.chdir(os.path.dirname(os.environ["DR_EXE_PATH"]))
            os.startfile(f'"{exe_path}"')
            os.chdir(os.environ["DSM_PATH"])

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
                message="Editing save data can potentially break a save file. Please back up your save before continuing."
            )
            self.userConfig["hasSeenEditWarning"] = True
            with open(os.path.join(os.environ["DSM_PATH"], "user_config.json"), "w", encoding="utf-8") as f:
                json.dump(self.userConfig, f, indent=4)

        SaveFileEdit(
            self,
            currentSave["chapter"],
            currentSave["slot"],
            self.appConfig["dw_invItems"],
            self.appConfig[f"chapter{currentSave['chapter']}"],
            self.appConfig,
            title=f"Editing save from Ch{currentSave['chapter']} slot {currentSave['slot']+1}"
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
            showerror(title="Error", message="Please select either a backup save or an active save to delete, not both.")
            self.chapterChange(self.chapterSelectFrame.getChapter())  # Update all frames to the current chapter
            return
        
        if currentBackup != -1:
            # Delete the selected backup save
            confirmDelete = askyesno(title="Delete Backup Save", message=f"Are you sure you want to delete the backup save '{currentBackup['selectedName']}'?")
            if confirmDelete is None:
                return
            if confirmDelete:
                os.remove(currentBackup["selectedPath"])
                self.chapterChange(self.chapterSelectFrame.getChapter())  # Update all frames to the current chapter
            return
        
        if currentSave != -1:
            # Delete the active save
            confirmDelete = askyesno(title="Delete Active Save", message=f"Are you sure you want to delete the active save in Chapter {currentSave['chapter']} Slot {currentSave['slot']+1}?")
            if confirmDelete is None:
                return
            if confirmDelete:
                if os.environ["DR_EXE_PATH"] in ["VIA_STEAM", "NOT_SET"]:
                    confirmSteamOpen = askyesno(title="Steam Cloud Check", message="If you are using Steam and have Steam Cloud enabled, it will automatically restore the save. However if you have the game open on the chapter select screen it will not restore the save. \nDo you want to open the game to ensure the save is deleted?")
                    if confirmSteamOpen is None:
                        return
                    if confirmSteamOpen:
                        self.launchGame()
                        showinfo(title="Opening Game", message="Opening the game to ensure the save is deleted. Please Press OK to continue when the game is open.")
                # Delete the save file
                savePath = os.path.join(os.environ["DR_SAVE_PATH"], f"filech{currentSave['chapter']}_{currentSave['slot']}")
                if os.path.exists(savePath):
                    os.remove(savePath)
            
            self.chapterChange(self.chapterSelectFrame.getChapter())  # Update all frames to the current chapter
            return

    def exit(self) -> None:
        print("Exiting app...")
        self.destroy()
        self.quit()
        
if __name__ == "__main__":
    print("Starting DELTARUNE Save Manager...")
    valid = validateFiles()
    if valid:
        appConfig = loadAppConfig()
        userConfig = loadUserConfig()
        setUpDirectories(appConfig)
        app = App(userConfig, appConfig)
        print("App running...")
        killSplash()
        app.mainloop()
    print("Exited.")