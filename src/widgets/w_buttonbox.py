from tkinter import Button, LabelFrame
from tkinter.constants import DISABLED, EW
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
