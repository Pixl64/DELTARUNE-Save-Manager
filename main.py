import os

from src.app import App
from src.config_load import loadAppConfig, loadUserConfig
from src.file_utils import getCurrentWorkingDirectory, setUpDirectories, validateFiles

runningDir, dataPath, killSplash = getCurrentWorkingDirectory()
# Global variables
os.environ["DSM_PATH"] = runningDir
os.environ["DSM_DATA_PATH"] = dataPath


if __name__ == "__main__":
    print("Starting DELTARUNE Save Manager...")
    valid = validateFiles(runningDir, killSplash)
    if valid:
        appConfig = loadAppConfig()
        userConfig = loadUserConfig()
        setUpDirectories(appConfig)
        app = App(userConfig, appConfig)
        print("App running...")
        killSplash()
        app.mainloop()
    print("Exited.")
