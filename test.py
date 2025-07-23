import os, sys, tkinter, subprocess, tempfile

if getattr(sys, 'frozen', False):
    runningDir = sys._MEIPASS
else:
    runningDir = os.path.dirname(os.path.abspath(__file__))

iconSrc = os.path.join(runningDir, "icon.ico")

# Check if the icon file exists and is readable


window = tkinter.Tk()
with tempfile.TemporaryDirectory() as tempDir:
    tmpIcon = os.path.join(tempDir, "appicon.ico")
    subprocess.run(
        f'copy "{iconSrc}" "{tmpIcon}"', 
        shell=True, 
        stdout=subprocess.DEVNULL
    )
    window.iconbitmap(tmpIcon)
window.mainloop()
