import os
import tempfile
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename

from filemanager import copyFile


def setWindowIcon(window: Tk):
    """Sets the window icon to the icon.ico file in the data directory"""
    # Copy the icon to a temporary directory to avoid issues with tkinter's iconbitmap
    # This is necessary because tkinter's iconbitmap does not work with frozen executables
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        iconSrc = os.path.join(os.environ["DSM_DATA_PATH"], "icon.ico")
        iconTmp = os.path.join(tempDir, "icon_temp.ico")
        copyFile(iconSrc, iconTmp)
        window.iconbitmap(iconTmp)


def createCutPath(path: str, entryWidth: int):
    """
    Creates a shortened version of the path for display purposes.
    If the path is longer than entryWidth, it will be cut and prefixed with '...'.
    """
    if len(path) > entryWidth:
        return "..." + path[-(entryWidth - 3) :]
    return path


def openFolderPicker(title: str, initialDir: str, entryWidth: int):
    directory = askdirectory(title=title, initialdir=initialDir)
    if not directory:
        return

    return [directory, createCutPath(directory, entryWidth)]


def openFilePicker(title: str, initialDir: str, entryWidth: int, filetypes=None):

    file = askopenfilename(title=title, initialdir=initialDir, filetypes=filetypes)
    if not file:
        return

    return [file, createCutPath(file, entryWidth)]
