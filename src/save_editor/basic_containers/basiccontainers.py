from tkinter import LabelFrame
from tkinter.constants import BOTH, END, LEFT

from src.save_editor.drag.draggabblelistbox import (
    DraggableListbox,
    DraggableScrollableListbox,
    DragManager,
)


class BasicContainer(LabelFrame):
    def __init__(
        self,
        parent,
        title: str,
        appConfig: dict,
        currentChapter: int,
        itemData: list,
        itemType: str,
        dragManager: DragManager,
    ):
        super().__init__(parent, text=title)

        self.itemListbox = DraggableListbox(
            self,
            dragManager,
            appConfig,
            chapter=currentChapter,
            allowInternalSwap=True,
            height=10,
        )
        self.itemListbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        # Insert items using IDs and tags
        for itemId in itemData:
            self.itemListbox.insertWithId(END, itemId, itemType)

    def getListbox(self):
        return self.itemListbox  # Return the actual listbox, not the container

    def getAllItems(self):
        """Get all items by their IDs"""
        items = []
        for i in range(self.itemListbox.size()):
            items.append(self.itemListbox.getItemId(i))
        return items


class LongItemContainer(LabelFrame):
    def __init__(
        self,
        parent,
        title: str,
        appConfig: dict,
        currentChapter: int,
        itemData: list,
        itemType: str,
        dragManager: DragManager,
    ):
        super().__init__(parent, text=title)

        self.itemListbox = DraggableScrollableListbox(
            self,
            dragManager,
            appConfig,
            currentChapter=currentChapter,
            allowInternalSwap=True,
            height=10,
        )
        self.itemListbox.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        # Insert items using IDs and tags
        for itemId in itemData:
            self.itemListbox.insertWithId(END, itemId, itemType)

    def getListbox(self):
        return (
            self.itemListbox.getListbox()
        )  # Return the actual listbox, not the container

    def getAllItems(self):
        """Get all items by their IDs"""
        items = []
        for i in range(self.itemListbox.listbox.size()):
            items.append(self.itemListbox.listbox.getItemId(i))
        return items
