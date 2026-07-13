import base64
from typing import TextIO


def encodeSave(saveFile: TextIO) -> str:
    """
    Encodes a save file, and returns a base64 encoded string. Decoded by `decodeSave`
    """
    fileText = saveFile.readlines()
    finalString = f"len\t{len(fileText)}\n"

    for i, line in enumerate(fileText):
        strippedLine = line.strip()
        if strippedLine != "0":
            finalString += f"{i}\t{strippedLine}\n"

    return base64.b64encode(finalString.encode("utf-8")).decode("utf-8")


def decodeSave(encoded: str) -> list:
    """
    Decodes a base64 encoded stripped save file, encoded by `encodeSave`
    """
    # Decode from base64
    decoded_str = base64.b64decode(encoded).decode("utf-8")
    lines = decoded_str.splitlines()

    # Check if it is a valid save.
    if not lines or not lines[0].startswith("len\t"):
        raise ValueError("Invalid encoded save format.")

    total_lines = int(lines[0].split("\t")[1])
    # Default to "0" for all lines
    file_lines = ["0"] * total_lines

    for line in lines[1:]:
        lineNumber, value = line.split("\t", 1)
        file_lines[int(lineNumber)] = value

    return file_lines
