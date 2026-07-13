from tkinter import LabelFrame

from src.save_editor.drag.draggablegrid import DraggableGrid
from src.save_editor.drag.dragmanager import DragManager


class Inventory(LabelFrame):
    def __init__(
        self,
        parent,
        title: str,
        appconfig: dict,
        currentChapter: int,
        inventoryData: list,
        dragManager: DragManager,
    ):
        super().__init__(parent, text=title)
        self.parent = parent
        self.appconfig = appconfig
        self.currentChapter = currentChapter
        self.storageData = inventoryData
        self.dragManager = dragManager

        # Create the DraggableGrid for the inventory items
        self.draggableGrid = DraggableGrid(
            self, self.dragManager, self.appconfig, self.currentChapter
        )
        self.draggableGrid.pack(pady=5)

        self.updateInventory(
            self.storageData
        )  # Populate the grid with initial storage data

    def updateInventory(self, newInventoryData: list):
        """Update the inventory with new storage data."""
        self.storageData = newInventoryData
        self.draggableGrid.populate_grid(self.storageData, "item")

    def getListboxes(self):
        """Return the list of DraggableListbox instances in the grid."""
        return self.draggableGrid.listboxes

    def getAllItems(self):
        """Get the selected items from all listboxes in the grid."""
        all_items = []
        for lb in self.draggableGrid.listboxes:
            for i in range(lb.size()):
                all_items.append(lb.getItemId(i))
        return all_items
