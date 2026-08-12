import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable
from tkinter import Tk
from tkinter.messagebox import askyesno, showerror
from typing import Any


def copyFile(src: str, dest: str):
    shutil.copy2(src, dest)


def getCurrentWorkingDirectory() -> tuple[str, str, Callable[[], None]]:
    """Returns the current working directory."""
    # Get current running directory
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        dataPath = sys._MEIPASS  # type: ignore
        runningDir = os.path.dirname(sys.executable)
        os.chdir(runningDir)

        # Import the pyi_splash module to close the splash screen
        import pyi_splash  # type: ignore

        def killSplash() -> None:
            pyi_splash.close()
    else:
        runningDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        dataPath = runningDir

        def killSplash() -> None:
            pass

    print(f"Running directory: {runningDir}")
    print(f"Data path: {dataPath}")

    return runningDir, dataPath, killSplash


def get_steam_install_location():
    try:
        result = subprocess.run(
            ["reg", "query", r"HKCU\Software\Valve\Steam", "/v", "SteamPath"],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            if "SteamPath" in line:
                return line.split("REG_SZ")[-1].strip()

    except subprocess.CalledProcessError:
        return None

    return None


def setUpDirectories(appConfig: dict[str, Any]) -> None:
    """Sets up the chapter directories in the backup path"""
    for i in range(appConfig["maximumChapter"]):
        if not os.path.exists(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i + 1}")):
            os.mkdir(os.path.join(os.environ["DSM_BKP_PATH"], f"CH{i + 1}"))


def validateFiles(runningDir: str, killSplash: Callable) -> bool:
    """Validates the existence of the app_config.json and user_config.json files, and creates the user_config.json if it does not exist."""
    from src.popup.first_time_setup import FirstTimeSetup

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


def validateChapterRun(
    dir: str, appConfig: dict, userConfig: dict[str, Any], chapter: int | None
) -> bool:
    """Validates that chapter music junctions exist when using chapter launching."""

    chapterLimits = (1, appConfig["maximumChapter"])

    for i in range(chapterLimits[0], chapterLimits[1] + 1):
        mus_dir = os.path.join(dir, f"chapter{i}_windows", "mus")

        if not is_link_or_junction(mus_dir):
            return False

    return True


def constructSave(savePath: str, lines: list):
    with open(savePath, "w") as f:
        f.write("\n".join(lines))


def is_link_or_junction(path):
    """
    Returns True if path is a symbolic link or Windows junction.
    """
    if os.path.islink(path):
        return True

    try:
        attrs = os.lstat(path).st_file_attributes
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except FileNotFoundError:
        return False


def link_music_to_chapters(root_dir):
    """
    Creates a 'mus' symlink inside every chapter*_windows folder
    pointing to the root 'mus' folder.

    Example:
        root_dir/
        ├── mus/
        ├── chapter1_windows/
        ├── chapter2_windows/
        └── chapter3_windows/

    Creates:
        chapter1_windows/mus -> ../mus
        chapter2_windows/mus -> ../mus
        etc.
    """

    music_dir = os.path.join(root_dir, "mus")

    if not os.path.isdir(music_dir):
        raise FileNotFoundError(f"Music folder not found: {music_dir}")

    chapter_pattern = re.compile(r"^chapter\d+_windows$")

    count = 0
    for name in os.listdir(root_dir):
        chapter_path = os.path.join(root_dir, name)

        if os.path.isdir(chapter_path) and chapter_pattern.match(name):
            link_path = os.path.join(chapter_path, "mus")

            # Already exists
            if os.path.exists(link_path) or os.path.islink(link_path):
                continue

            # Create relative symlink

            subprocess.run(
                ["cmd", "/c", "mklink", "/J", link_path, music_dir],
                shell=False,
                check=False,
            )
            count += 1

    return f"Created {count} music links in chapter folders."


def remove_music_links(root_dir):
    """
    Removes mus symlinks/junctions from every chapter*_windows folder.
    Leaves real folders untouched.
    """

    chapter_pattern = re.compile(r"^chapter\d+_windows$")

    count = 0
    skipped = 0
    failed = 0
    for name in os.listdir(root_dir):
        chapter_dir = os.path.join(root_dir, name)

        if not (os.path.isdir(chapter_dir) and chapter_pattern.match(name)):
            continue

        music_link = os.path.join(chapter_dir, "mus")

        if is_link_or_junction(music_link):
            try:
                os.rmdir(music_link)
                count += 1
            except OSError:
                failed += 1

        elif os.path.exists(music_link):
            skipped += 1
        else:
            continue

    return f"Removed {count} music links. Skipped {skipped} real folders. Failed to remove {failed} links."


def get_deltarune_location(appID: int) -> str:
    if os.environ["DR_EXE_PATH"] == "VIA_STEAM":
        steam_location = get_steam_install_location()
        if not steam_location:
            raise FileNotFoundError("Steam installation not found.")

        steam_library_data = os.path.join(
            steam_location, "steamapps", "libraryfolders.vdf"
        )

        if not os.path.exists(steam_library_data):
            raise FileNotFoundError(
                "Steam libraryfolders.vdf not found. Please ensure Steam is installed and try again."
            )
        data = valve_data_to_dict(steam_library_data)

        for lib in data["libraryfolders"].values():
            if not isinstance(lib, dict):
                continue

            manifest = os.path.join(
                lib["path"], "steamapps", f"appmanifest_{appID}.acf"
            )

            if os.path.exists(manifest):
                return os.path.join(lib["path"], "steamapps", "common", "DELTARUNE")

        raise FileNotFoundError(
            "DELTARUNE installation not found in any Steam library. Please ensure the game is installed and try again."
        )

    else:
        if not os.path.exists(os.environ["DR_EXE_PATH"]):
            raise FileNotFoundError(
                f"Game executable path does not exist: {os.environ['DR_EXE_PATH']}"
            )
        return os.path.dirname(os.environ["DR_EXE_PATH"])


def launch_game(appConfig: dict, userConfig: dict, chapter: int | None) -> None:
    try:
        deltaruneLocation = get_deltarune_location(appConfig["appID"])
    except FileNotFoundError as e:
        showerror(title="Error", message=str(e))
        return

    if os.environ["DR_EXE_PATH"] == "VIA_STEAM":
        # If the user has selected to launch a specific chapter, validate that the /mus folder exists for that chapter
        if (
            chapter is not None
            and chapter > 0
            and chapter <= appConfig["maximumChapter"]
        ):
            valid = validateChapterRun(
                deltaruneLocation, appConfig, userConfig, chapter
            )

            if not valid:
                if not askyesno(
                    title="Error",
                    message=f"Cannot launch chapter {chapter} because the /mus folder is not linked. Do you want to link the mus /folder to all chapters now? (This will modify your DELTARUNE installation. It is reversable in the settings.)",
                    icon="error",
                ):
                    return

                link_music_to_chapters(deltaruneLocation)

            steamLocation = get_steam_install_location()
            if not steamLocation:
                showerror(
                    title="Error",
                    message="Steam installation not found. Please ensure Steam is installed and try again.",
                )
                return

            steam_exe = os.path.join(steamLocation, "Steam.exe")

            os.startfile(
                f"{steam_exe}",
                arguments=rf"-applaunch {appConfig['appID']} -game chapter{chapter}_windows\data.win launcher",
            )
        else:
            os.startfile(f"steam://run/{appConfig['appID']}")

        return

    if not os.path.exists(os.environ["DR_EXE_PATH"]):
        showerror(
            title="Error",
            message=f"Game executable path does not exist. \nPlease reset it in the settings.\n{os.environ['DR_EXE_PATH']}",
        )
        return
    else:
        exe_path = os.environ["DR_EXE_PATH"]
        if (
            chapter is not None
            and chapter > 0
            and chapter <= appConfig["maximumChapter"]
        ):
            subprocess.Popen(
                [
                    exe_path,
                    "-game",
                    "data.win",
                    "launcher",
                ],
                cwd=rf"{os.path.dirname(exe_path)}\chapter{chapter}_windows",
            )
        else:
            subprocess.Popen(
                [
                    exe_path,
                    "-game",
                    "data.win",
                    "launcher",
                ],
                cwd=rf"{os.path.dirname(exe_path)}",
            )


def valve_data_to_dict(filename):
    """Convert a simple Steam VDF/ACF file into a Python dictionary."""

    with open(filename, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    stack = []
    root = {}
    current = root
    pending_key = None

    for line in lines:
        if line == "{":
            # Start a new object for the previous key
            new_dict = {}
            current[pending_key] = new_dict
            stack.append(current)
            current = new_dict
            pending_key = None

        elif line == "}":
            # Return to the parent object
            current = stack.pop()

        else:
            # Split quoted strings
            parts = [p.strip() for p in line.split('"')]
            strings = [p for p in parts if p]

            if len(strings) == 1:
                # A key whose value is another object
                pending_key = strings[0]

            elif len(strings) >= 2:
                # A normal key/value pair
                current[strings[0]] = strings[1]

    return root
