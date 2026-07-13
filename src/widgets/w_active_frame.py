from tkinter import Frame, Listbox

from src.utils import getActiveDisplayData


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
