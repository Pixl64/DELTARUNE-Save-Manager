import ctypes
import os
import tempfile
from tkinter import Tk, Toplevel

from src.file_utils import copyFile


def setWindowIcon(window: Tk | Toplevel) -> None:
    """Sets the window icon to the icon.ico file in the data directory"""
    # Copy the icon to a temporary directory to avoid issues with tkinter's iconbitmap
    # This is necessary because tkinter's iconbitmap does not work with frozen executables
    with tempfile.TemporaryDirectory("DSM") as tempDir:
        iconSrc = os.path.join(os.environ["DSM_DATA_PATH"], "icon.ico")
        iconTmp = os.path.join(tempDir, "icon_temp.ico")
        copyFile(iconSrc, iconTmp)
        window.iconbitmap(iconTmp)


def set_window_middle(window: Tk, width: int, height: int) -> None:
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    middle = screensize[0] // 2, screensize[1] // 2
    add = middle[0] - width // 2, middle[1] - height // 2
    window.geometry(f"{width}x{height}+{add[0]}+{add[1]}")
