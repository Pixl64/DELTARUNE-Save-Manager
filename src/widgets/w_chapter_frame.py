from tkinter import Frame, IntVar, Label, Spinbox
from tkinter.constants import LEFT, NW
from typing import Callable


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
