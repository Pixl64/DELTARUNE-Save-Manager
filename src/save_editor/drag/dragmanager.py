from dataclasses import dataclass
from tkinter import RAISED, Label, Toplevel
from tkinter.constants import END
from typing import TYPE_CHECKING, Optional

from src.utils import can_equip

if TYPE_CHECKING:
    from src.save_editor.drag.draggabblelistbox import DraggableListbox


@dataclass(slots=True)
class DragInfo:
    listbox: DraggableListbox
    index: int
    text: str
    tag: str | None
    id: int | None


class DragManager:
    """Manages drag and drop operations between DraggableListbox instances."""

    def __init__(self, root, appConfig=None):
        self.root = root
        self.appConfig = appConfig or {}
        self.colors = appConfig.get("colors", {}) if appConfig else {}
        self.listboxes = []

        # Variables to track dragging
        self.drag: DragInfo | None = None

        # Create drag visualization window (initially hidden)
        self.dragWindow = None

    def registerListbox(self, listbox: DraggableListbox) -> None:
        """Register a listbox with the drag manager."""
        self.listboxes.append(listbox)

    def createDragWindow(self) -> None:
        """Create the drag visualization window"""
        self.dragWindow = Toplevel(self.root)
        self.dragWindow.wm_overrideredirect(True)
        self.dragWindow.wm_attributes("-topmost", True)
        defaultColor = self.colors.get("dragWindowDefault", "lightblue")
        self.dragWindow.configure(bg=defaultColor)

        self.dragLabel = Label(
            self.dragWindow,
            text="",
            bg=defaultColor,
            fg="black",
            font=("Arial", 9),
            padx=8,
            pady=4,
            relief=RAISED,
            borderwidth=2,
        )
        self.dragLabel.pack()
        self.dragWindow.withdraw()

    def startDrag(self, sourceListbox: DraggableListbox, event) -> None:
        """Start a drag operation"""
        index = sourceListbox.nearest(event.y)

        if index >= 0 and index < sourceListbox.size():
            drag = DragInfo(
                listbox=sourceListbox,
                index=index,
                text=sourceListbox.get(index),
                tag=sourceListbox.getItemTag(index),
                id=sourceListbox.getItemId(index),
            )

            # Only allow dragging items with IDs
            if drag.id is None:
                return

            self.drag = drag

            # Visual feedback
            sourceListbox.selection_clear(0, END)
            sourceListbox.selection_set(index)
            sourceListbox.config(cursor="hand2")

            # Create drag window if it doesn't exist
            if self.dragWindow is None:
                self.createDragWindow()

            # Show and position the drag window with tag and ID info
            displayText = f"{self.drag.text}"
            if self.drag.tag is not None:
                displayText += f" [ {self.drag.tag} ]"
            if self.drag.id is not None:
                displayText += f" (ID: {self.drag.id})"

            self.dragLabel.config(text=displayText)
            defaultColor = self.colors.get("dragWindowDefault", "lightblue")
            self._updateDragWindowStyle(defaultColor)

            x, y = self.root.winfo_pointerxy()
            if self.dragWindow:
                self.dragWindow.geometry(f"+{x + 10}+{y + 10}")
                self.dragWindow.deiconify()  # Show the window

            # Highlight valid drop zones
            self._highlightValidDropZones()

    def onDrag(self, event) -> None:
        """Handle drag motion"""
        if self.drag is None:
            return
        # Handle drag motion if we have an active drag
        if (
            self.drag.listbox is not None
            and self.dragWindow is not None
            and self.drag.index is not None
        ):
            # Update drag window position
            x, y = self.root.winfo_pointerxy()
            self.dragWindow.geometry(f"+{x + 10}+{y + 10}")

            # Get the widget under the mouse cursor
            widget = self.root.winfo_containing(x, y)

            actualListbox = self._findActualListbox(widget)

            # Clear all selections first
            for listbox in self.listboxes:
                listbox.selection_clear(0, END)

            # Check if we're over a registered listbox
            if actualListbox is not None:
                # Convert screen coordinates to widget coordinates
                relativeY = y - actualListbox.winfo_rooty()

                # Get the index at this position
                index = actualListbox.nearest(relativeY)

                if 0 <= index < actualListbox.size():
                    targetId = actualListbox.getItemId(index)
                    if targetId is None:
                        self._setDragStateColor("invalid")
                        return
                    if self._canDrop(actualListbox, index):
                        actualListbox.selection_set(index)
                        self._setDragStateColor("valid")
                        return

                    self._setDragStateColor("invalid")

    def onDrop(self, event) -> None:
        """Handle drop operation"""
        if self.drag is None:
            return
        if self.drag.listbox is not None and self.drag.index is not None:
            # Get the widget under the mouse cursor
            x, y = self.root.winfo_pointerxy()
            widget = self.root.winfo_containing(x, y)
            targetListbox = self._findActualListbox(widget)

            # Check if dropping on a registered listbox (must be registered with THIS drag manager)
            if targetListbox is not None and targetListbox in self.listboxes:
                relativeY = y - targetListbox.winfo_rooty()
                dropIndex = targetListbox.nearest(relativeY)

                # Validate drop conditions
                if (
                    0 <= dropIndex < targetListbox.size()
                    and self.drag.id is not None
                    and targetListbox.getItemId(dropIndex) is not None
                ):
                    if self._canDrop(targetListbox, dropIndex):
                        self._swapItems(
                            self.drag.listbox, self.drag.index, targetListbox, dropIndex
                        )

        # Clear all highlights
        self._clearAllHighlights()

        # Hide the drag window
        if self.dragWindow:
            self.dragWindow.withdraw()

        # Reset drag state and cursor
        self._resetDragState()

    def onEnterListbox(self, event) -> None:
        """Handle mouse entering a listbox during drag"""
        if self.drag is None:
            return
        if self.drag.listbox is not None:
            event.widget.config(cursor="hand2")

    def onLeaveListbox(self, event) -> None:
        """Handle mouse leaving a listbox during drag"""
        if self.drag is None:
            return
        if self.drag.listbox is not None:
            if event.widget != self.drag.listbox:
                event.widget.config(cursor="")

    def _canDrop(
        self,
        targetListbox,
        targetIndex,
    ):
        if self.drag is None:
            return False

        if self.drag.listbox is None or self.drag.index is None:
            return False

        if targetListbox.getItemId(targetIndex) is None:
            return False

        if (
            targetListbox == self.drag.listbox
            and not self.drag.listbox.allowInternalSwap
        ):
            return False

        if not self._canEquipSwap(
            self.drag.listbox,
            self.drag.index,
            targetListbox,
            targetIndex,
        ):
            return False

        return self.canSwapItems(
            self.drag.listbox,
            self.drag.index,
            targetListbox,
            targetIndex,
        )

    def _canEquipSwap(self, sourceListbox, sourceIndex, targetListbox, targetIndex):
        sourceOwner = getattr(sourceListbox, "owner", None)
        targetOwner = getattr(targetListbox, "owner", None)

        sourceItemId = sourceListbox.getItemId(sourceIndex)
        sourceItemTag = sourceListbox.getItemTag(sourceIndex)

        targetItemId = targetListbox.getItemId(targetIndex)
        targetItemTag = targetListbox.getItemTag(targetIndex)

        # Moving source item into target slot
        if targetOwner is not None:
            if not can_equip(
                targetListbox.dw_invItems,
                sourceItemId,
                sourceItemTag,
                targetOwner,
            ):
                return False

        # Moving target item into source slot
        if sourceOwner is not None:
            if not can_equip(
                sourceListbox.dw_invItems,
                targetItemId,
                targetItemTag,
                sourceOwner,
            ):
                return False

        return True

    def canSwapItems(
        self,
        sourceListbox: DraggableListbox,
        sourceIndex: int,
        targetListbox: DraggableListbox,
        targetIndex: int,
    ) -> bool:
        """Check if two items can be swapped based on their tags"""
        sourceTag = sourceListbox.getItemTag(sourceIndex)
        targetTag = targetListbox.getItemTag(targetIndex)

        # Items can be swapped if:
        # 1. Both have no tags (None)
        # 2. Both have the same tag
        return sourceTag == targetTag

    def _swapItems(
        self,
        sourceListbox: DraggableListbox,
        sourceIndex: int,
        targetListbox: DraggableListbox,
        targetIndex: int,
    ) -> None:
        # Perform the swap
        startId = sourceListbox.getItemId(sourceIndex)
        dropId = targetListbox.getItemId(targetIndex)
        startTag = sourceListbox.getItemTag(sourceIndex)
        dropTag = targetListbox.getItemTag(targetIndex)

        if startId is None or dropId is None:
            return

        sourceListbox.setItemId(sourceIndex, dropId)
        sourceListbox.setItemTag(sourceIndex, dropTag)

        targetListbox.setItemId(targetIndex, startId)
        targetListbox.setItemTag(targetIndex, startTag)

        # Update selection
        for listbox in self.listboxes:
            listbox.selection_clear(0, END)
        targetListbox.selection_set(targetIndex)

    def _findActualListbox(self, widget) -> Optional[DraggableListbox]:
        """Find the actual listbox widget (handles scrollable containers)"""
        from src.save_editor.drag.draggabblelistbox import DraggableListbox

        # If it's a DraggableListbox, return it
        if isinstance(widget, DraggableListbox):
            return widget

        # If it's a container (like DraggableScrollableListbox), check for listbox attribute
        if hasattr(widget, "listbox") and isinstance(widget.listbox, DraggableListbox):
            return widget.listbox

        # Check if the widget is a child of a registered listbox
        if widget in self.listboxes:
            return widget

        return None

    def _highlightValidDropZones(self) -> None:
        """Highlight individual valid/invalid drop slots."""

        if self.drag is None:
            return

        for listbox in self.listboxes:
            listbox.clearItemHighlights()

            for i in range(listbox.size()):
                targetId = listbox.getItemId(i)

                if targetId is None:
                    continue

                if self._canDrop(listbox, i):
                    listbox.setItemHighlight(
                        i, self.colors.get("dropHighlight", "lightgreen")
                    )
                else:
                    listbox.setItemHighlight(
                        i, self.colors.get("invalidHighlight", "lightcoral")
                    )

    def _clearAllHighlights(self) -> None:
        for listbox in self.listboxes:
            listbox.clearItemHighlights()

    def _updateDragWindowStyle(self, color: str) -> None:
        """Update drag window background color and relief style."""
        if self.dragWindow:
            self.dragWindow.configure(bg=color)
            self.dragLabel.configure(bg=color, relief=RAISED)

    def _setDragStateColor(self, key: str):
        color = self.colors.get(
            {
                "default": "dragWindowDefault",
                "valid": "dropHighlight",
                "invalid": "invalidHighlight",
            }[key],
            {
                "default": "lightblue",
                "valid": "lightgreen",
                "invalid": "lightcoral",
            }[key],
        )

        self._updateDragWindowStyle(color)

    def _cancelDrag(self) -> None:
        """Cancel the current drag operation"""
        # Clear all highlights
        self._clearAllHighlights()

        # Hide the drag window
        if self.dragWindow:
            self.dragWindow.withdraw()

        # Reset drag state and cursor
        self._resetDragState()

    def _resetDragState(self):
        if self.drag is not None and self.drag.listbox:
            self.drag.listbox.config(cursor="")
        self.drag = None
