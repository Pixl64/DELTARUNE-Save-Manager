import tkinter.messagebox as messagebox
from tkinter import Frame, Widget

from src.save_editor.drag.draggabblelistbox import DraggableListbox
from src.save_editor.drag.dragmanager import DragManager


class DraggableGrid(Frame):
    """A grid of draggable items with context menu support."""

    def __init__(
        self,
        parent: Widget,
        dragManager: DragManager,
        appConfig: dict,
        chapter=1,
        **kwargs,
    ):
        if "colors" not in appConfig:
            appConfig["colors"] = {}
            appConfig["colors"]["selectBackground"] = "#00c5ff"

        super().__init__(parent, **kwargs)

        # Configuration
        # TODO: Remove unused ones
        self.dragManager = dragManager
        self.appConfig = appConfig
        self.listboxes = []
        self.dw_invItems = appConfig.get("dw_invItems", {}) if appConfig else {}
        self.chapter = chapter
        self.colors = appConfig.get("colors", {}) if appConfig else {}

        self.rows = 6
        self.columns = 2

        self.originalBg = self.cget("bg")  # Store original background color
        self._build_widgets()

    def _build_widgets(self):
        """Build the grid of items."""

        for r in range(self.rows):
            row_listboxes = []
            for c in range(self.columns):
                lb = DraggableListbox(
                    self,
                    self.dragManager,
                    self.appConfig,
                    chapter=self.chapter,
                    allowInternalSwap=True,
                    height=1,
                    width=18,
                )
                lb.grid(row=r, column=c, padx=2, pady=1, sticky="ew")
                row_listboxes.append(lb)
            self.listboxes.extend(row_listboxes)

    def populate_grid(self, items: list, item_tag: str):
        # Check if available_items is empty
        if not items:
            messagebox.showinfo("Info", "No items available to display.")
            return

        if len(items) != len(self.listboxes):
            messagebox.showwarning(
                "Warning",
                f"Number of items ({len(items)}) does not match the number of listboxes ({len(self.listboxes)}).",
            )

        # Fill the grid with items
        for index, lb in enumerate(self.listboxes):
            lb.deleteItem(0)
            lb.insertWithId(0, items[index], item_tag)
