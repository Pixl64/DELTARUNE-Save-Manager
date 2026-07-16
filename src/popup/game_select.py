import os
from tkinter import Frame, Label
from tkinter.constants import LEFT, NW, TOP
from tkinter.messagebox import showerror
from tkinter.simpledialog import Dialog

from src.gui_utils import setWindowIcon
from src.widgets.w_selectors import (
    GameSelectSelectorFrame,
)


class GameSelectPopup(Dialog):
    def __init__(self, parent, title="", initialDir="."):
        self.FileDialogueTitle = title
        self.initialDir = initialDir
        self.entryWidth = 40

        # Initialize the dialog
        super().__init__(parent, title=title)

    # Function to create the body of the dialog
    def body(self, master):
        setWindowIcon(self)
        self.winfo_toplevel().resizable(False, False)
        self.minsize(width=250, height=100)

        self.mainFrame = Frame(master)

        self.descriptionLabel = Label(
            self.mainFrame,
            text="Please select the DELTARUNE game location.",
            wraplength=350,
            justify=LEFT,
        )

        self.gameSelectFrame = GameSelectSelectorFrame(
            self.mainFrame,
            self.initialDir,
            entryWidth=self.entryWidth,
        )
        self.descriptionLabel.pack(side=TOP, anchor=NW, padx=5, pady=5)
        self.gameSelectFrame.pack(side=TOP, anchor=NW, padx=5, pady=5)

        self.mainFrame.pack()

    def validate(self):
        gameData = self.gameSelectFrame.getValue()

        if gameData["type"] == "custom":
            if not os.path.exists(gameData["path"]):
                showerror(
                    title="Error",
                    message=f"Game executable location does not exist.\n{gameData['path']}",
                )
                return False

        return True

    def apply(self):
        self.result = {
            "launchData": self.gameSelectFrame.getValue(),
            "runGameFollowsActiveChapter": self.gameSelectFrame.getFollowActiveChapter(),
        }
        return
