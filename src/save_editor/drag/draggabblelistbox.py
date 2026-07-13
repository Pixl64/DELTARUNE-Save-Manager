import tkinter.messagebox as messagebox
from tkinter import Frame, Listbox, Menu, Scrollbar, Widget
from tkinter.constants import BOTH, END, LEFT, RIGHT, SINGLE, VERTICAL, Y
from typing import Optional, Union

from src.save_editor.drag.dragmanager import DragManager
from src.utils import (
    CATEGORY_MAP,
    filter_and_group_items_by_chapter,
    format_item_type,
    get_item_name,
)


class DraggableListbox(Listbox):
    """A Listbox with drag-and-drop functionality and context menu support."""

    def __init__(
        self,
        parent: Widget,
        dragManager: DragManager,
        appConfig: dict,
        chapter=1,
        allowInternalSwap=True,
        **kwargs,
    ):
        if "colors" not in appConfig:
            appConfig["colors"] = {}
            appConfig["colors"]["selectBackground"] = "#00c5ff"

        # Configuration
        self.dragManager = dragManager
        self.appConfig = appConfig or {}
        self.dw_invItems = appConfig.get("dw_invItems", {}) if appConfig else {}
        self.chapter = chapter
        self.allowInternalSwap = allowInternalSwap
        self.colors = appConfig.get("colors", {}) if appConfig else {}
        self.owner: Optional[str] = None

        kwargs.setdefault("selectbackground", self.colors["selectBackground"])

        super().__init__(parent, selectmode=SINGLE, **kwargs)

        # Item tracking
        self.itemTags = {}  # Maps index to item tag (type)
        self.itemIds = {}  # Maps index to item ID

        self.originalBg = self.cget("bg")  # Store original background color

        self.setupBindings()

    def setupBindings(self) -> None:
        """Set up mouse event bindings for drag-and-drop and context menu."""
        self.bind(
            "<Button-1>", self._onStartDrag
        )  # Left mouse button press (Listbox drag start)
        self.bind(
            "<B1-Motion>", self._onDrag
        )  # Mouse movement with button held down (Dragging listbox item)
        self.bind(
            "<ButtonRelease-1>", self._onDrop
        )  # Left mouse button release (Dropping listbox item)
        self.bind("<Enter>", self._onEnterListbox)  # Mouse enters listbox
        self.bind("<Leave>", self._onLeaveListbox)  # Mouse leaves listbox
        self.bind(
            "<Button-3>", self._replaceItemClickEvent
        )  # Right mouse button press (Context menu)

    def _replaceItemClickEvent(self, event) -> None:
        """Handle right-click event to show context menu for item replacement."""
        index = self.nearest(
            event.y
        )  # Get the index of the item under the mouse cursor

        if 0 <= index < self.size():
            # Highlight the right-clicked item
            self.selection_clear(0, END)
            self.selection_set(index)

            # Get all items of this type
            itemTag = self.getItemTag(index)
            if itemTag:
                category = CATEGORY_MAP.get(itemTag, "items")
                availableItems = self.dw_invItems.get(category, {})

                if not availableItems:
                    messagebox.showwarning("No Items", f"No {itemTag} items available")
                    return

                self._showContextMenu(event, index, itemTag, availableItems)

    def _showContextMenu(
        self, event, index: int, itemTag: str, availableItems: dict
    ) -> None:
        """Show context menu for replacing an item with another of the same item type."""
        selectColor = self.colors["selectBackground"]
        context_menu = Menu(
            self, tearoff=0, activebackground=selectColor, activeborderwidth=0
        )

        current_item_id = self.getItemId(index)
        current_name = get_item_name(self.dw_invItems, current_item_id, itemTag)
        context_menu.add_command(
            label=f"Current: {current_name} (ID: {current_item_id})",
            state="disabled",
            foreground="gray",
        )
        context_menu.add_separator()

        replace_menu = Menu(
            context_menu, tearoff=0, activebackground=selectColor, activeborderwidth=0
        )
        replace_menu.add_command(
            label="Clear Slot", command=lambda: self.setItemId(index, 0)
        )
        replace_menu.add_separator()

        chapters = filter_and_group_items_by_chapter(
            availableItems, self.appConfig, self.chapter, itemTag
        )

        multiple_chapters = len(chapters) > 1
        for chapter, chapter_items in chapters.items():
            if multiple_chapters:
                chapter_menu = Menu(
                    replace_menu,
                    tearoff=0,
                    activebackground=selectColor,
                    activeborderwidth=0,
                )
                for itemId, itemName in chapter_items:
                    chapter_menu.add_command(
                        label=f"ID {itemId}: {itemName}",
                        command=lambda id_val=itemId: self.setItemId(index, id_val),
                    )
                replace_menu.add_cascade(label=f"Chapter {chapter}", menu=chapter_menu)
            else:
                for itemId, itemName in chapter_items:
                    replace_menu.add_command(
                        label=f"ID {itemId}: {itemName}",
                        command=lambda id_val=itemId: self.setItemId(index, id_val),
                    )

        context_menu.add_cascade(
            label=f"Replace {format_item_type(itemTag)}...", menu=replace_menu
        )
        context_menu.add_separator()
        context_menu.add_command(label="Cancel", command=lambda: context_menu.unpost())

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def insertWithId(self, index: Union[int, str], itemId: int, tag: str) -> None:
        """Insert an item with an associated ID and tag, converting ID to display name"""
        # Get item name from app_config based on tag
        displayText = get_item_name(self.dw_invItems, itemId, tag)
        self.insert(index, displayText)

        # Get the actual index after insertion
        if index == END:
            actualIndex: int = self.size() - 1
        else:
            actualIndex = int(index)

        self.itemIds[actualIndex] = itemId
        self.itemTags[actualIndex] = tag
        self._updateIndices()

    def deleteItem(self, index: int) -> None:
        """Delete an item and update internal tracking indices."""
        if index in self.itemTags:
            del self.itemTags[index]
        if index in self.itemIds:
            del self.itemIds[index]
        self.delete(index)
        self._updateIndices()

    def _updateIndices(self) -> None:
        """Update tag and ID indices after insertions/deletions."""
        newTags = {
            i: self.itemTags[i] for i in range(self.size()) if i in self.itemTags
        }
        newIds = {i: self.itemIds[i] for i in range(self.size()) if i in self.itemIds}
        self.itemTags = newTags
        self.itemIds = newIds

    def getItemTag(self, index: int) -> Optional[str]:
        """Get the tag for an item at the given index"""
        return self.itemTags.get(index, None)

    def getItemId(self, index: int) -> Optional[int]:
        """Get the ID for an item at the given index"""
        return self.itemIds.get(index, None)

    def setItemTag(self, index: int, tag: Optional[str]) -> None:
        """Set the tag for an item at the given index"""
        self.itemTags[index] = tag

    def setItemId(self, index: int, itemId: int) -> None:
        old_colour = self.itemcget(index, "bg")

        self.itemIds[index] = itemId
        tag = self.getItemTag(index) or "item"

        displayText = get_item_name(self.dw_invItems, itemId, tag)
        self.delete(index)
        self.insert(index, displayText)

        if old_colour:
            self.itemconfig(index, bg=old_colour)

    def setItemHighlight(self, index: int, colour: str | None = None) -> None:
        """Highlight a specific item row."""
        if 0 <= index < self.size():
            if colour:
                self.itemconfig(index, bg=colour)
            else:
                self.itemconfig(index, bg=self.originalBg)

    def clearItemHighlights(self) -> None:
        """Reset all item row colours."""
        for i in range(self.size()):
            self.itemconfig(i, bg=self.originalBg)

    # Event handlers for drag and drop
    def _onStartDrag(self, event) -> None:
        self.dragManager.startDrag(self, event)

    def _onDrag(self, event) -> None:
        self.dragManager.onDrag(event)

    def _onDrop(self, event) -> None:
        self.dragManager.onDrop(event)

    def _onEnterListbox(self, event) -> None:
        self.dragManager.onEnterListbox(event)

    def _onLeaveListbox(self, event) -> None:
        self.dragManager.onLeaveListbox(event)


class DraggableScrollableListbox(Frame):
    """A scrollable wrapper for DraggableListbox with vertical scrollbar."""

    def __init__(
        self,
        parent,
        dragManager: DragManager,
        appConfig: dict,
        currentChapter=1,
        allowInternalSwap=True,
        **kwargs,
    ):
        super().__init__(parent)

        # Create listbox and scrollbar
        self.listbox = DraggableListbox(
            self,
            dragManager,
            appConfig,
            chapter=currentChapter,
            allowInternalSwap=allowInternalSwap,
            **kwargs,
        )
        self.scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Pack components
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)

    # Delegate methods to the inner listbox
    def insertWithId(self, index: Union[int, str], itemId: int, tag: str) -> None:
        """Insert an item with ID and tag."""
        self.listbox.insertWithId(index, itemId, tag)

    def deleteItem(self, index: int) -> None:
        """Delete an item."""
        self.listbox.deleteItem(index)

    def getItemTag(self, index: int) -> Optional[str]:
        """Get item tag at index."""
        return self.listbox.getItemTag(index)

    def getItemId(self, index: int) -> Optional[int]:
        """Get item ID at index."""
        return self.listbox.getItemId(index)

    def setItemTag(self, index: int, tag: str) -> None:
        """Set item tag at index."""
        self.listbox.setItemTag(index, tag)

    def setItemId(self, index: int, itemId: int) -> None:
        """Set item ID at index."""
        self.listbox.setItemId(index, itemId)

    def getListbox(self) -> DraggableListbox:
        """Get the inner listbox widget."""
        return self.listbox
