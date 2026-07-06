import os

from filemanager import copyFile

fp = os.path.dirname(os.path.abspath(__file__))
buildPath = os.path.join(fp, "build")
distPath = os.path.join(fp, "dist")
os.chdir(fp)

buildFileName = "main.py"
iconName = "icon.ico"

args = {
    "name": "DSM_v0.1",
    # Max size: 760w 480h
    "splash": "splash2.png",
    "onefile": "",
    "clean": "",
    "windowed": "",
    #"specpath": specPath,
    "hide-console": "hide-early",
    "hidden-import": "pyi_splash",
}

includedFiles = [
    iconName,
    "app_config.json",
]

# Copy included files to the INTERNAL directory
for f in includedFiles:
    src = os.path.join(fp, f)
    dest = os.path.join(fp, "INTERNAL", f)
    if not os.path.exists(os.path.join(fp, "INTERNAL")):
        os.makedirs(os.path.join(fp, "INTERNAL"))
    copyFile(src, dest)

# Construct the command string, if a value is None, just put the key value
# If a value is not None, put the key and value together
runString = f"pyinstaller -i {iconName} {' '.join(f'--{k}' for k, v in args.items() if v == "")} --add-data \"INTERNAL:.\" {' '.join(f'--{k} {v}' for k, v in args.items() if v != "")} {buildFileName}"

print(f"Running: {runString}")

os.system(runString)
# Move the generated executable to the main directory
if os.path.exists(distPath):
    for item in os.listdir(distPath):
        itemPath = os.path.join(distPath, item)
        if os.path.isfile(itemPath):
            newPath = os.path.join(fp, item)
            if os.path.exists(newPath):
                os.remove(newPath)
            os.rename(itemPath, newPath)
            print("Moved executable to main directory")
    # Remove the dist directory
    os.rmdir(distPath)
else:
    print("No dist directory found, nothing to move.")

if os.path.exists(os.path.join(fp, args["name"] + ".spec")):
    os.remove(os.path.join(fp, args["name"] + ".spec"))
    print(f"Removed spec file: {args['name']}.spec")

"""
usage: pyinstaller [-h] [-v] [-D] [-F] 
    [--specpath DIR] 
    [-n NAME] 
    [--contents-directory CONTENTS_DIRECTORY] 
    [--add-data SOURCE:DEST] 
    [--add-binary SOURCE:DEST] 
    [-p DIR] 
    [--hidden-import MODULENAME] 
    [--collect-submodules MODULENAME]
    [--collect-data MODULENAME] 
    [--collect-binaries MODULENAME] 
    [--collect-all MODULENAME] 
    [--copy-metadata PACKAGENAME] 
    [--recursive-copy-metadata PACKAGENAME] 
    [--additional-hooks-dir HOOKSPATH]
    [--runtime-hook RUNTIME_HOOKS] 
    [--exclude-module EXCLUDES] 
    [--splash IMAGE_FILE] 
    [-d {all,imports,bootloader,noarchive}] 
    [--optimize LEVEL] 
    [--python-option PYTHON_OPTION] 
    [-s] 
    [--noupx] 
    [--upx-exclude FILE] 
    [-c] 
    [-w]      
    [--hide-console {minimize-early,minimize-late,hide-late,hide-early}] 
    [-i <FILE.ico or FILE.exe,ID or FILE.icns or Image or "NONE">] 
    [--disable-windowed-traceback] 
    [--version-file FILE] 
    [--manifest <FILE or XML>]
    [-m <FILE or XML>] 
    [-r RESOURCE] 
    [--uac-admin] 
    [--uac-uiaccess] 
    [--argv-emulation] 
    [--osx-bundle-identifier BUNDLE_IDENTIFIER] 
    [--target-architecture ARCH] 
    [--codesign-identity IDENTITY] 
    [--osx-entitlements-file FILENAME]  
    [--runtime-tmpdir PATH] 
    [--bootloader-ignore-signals] 
    [--distpath DIR] 
    [--workpath WORKPATH] 
    [-y] 
    [--upx-dir UPX_DIR] 
    [--clean] 
    [--log-level LEVEL]
scriptname [scriptname ...]


"""