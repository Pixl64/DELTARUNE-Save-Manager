from tkinter import Frame, Label, LabelFrame
from tkinter.constants import BOTTOM, LEFT, RIGHT, X

from src.save_editor.basic_containers.storage_viewall import open_view_all_window
from src.save_editor.drag.draggablegrid import DraggableGrid
from src.save_editor.drag.dragmanager import DragManager


class Storage(LabelFrame):
    def __init__(
        self,
        parent,
        title: str,
        appconfig: dict,
        currentChapter: int,
        storageData: list,
        dragManager: DragManager,
    ):
        super().__init__(parent, text=title)
        self.parent = parent
        self.appconfig = appconfig
        self.currentChapter = currentChapter
        self.storageData = storageData
        self.dragManager = dragManager
        self.currentPage = 0

        self.ITEMS_PER_PAGE = 12

        self._build_widgets()
        self._load_page()

    def _build_widgets(self):
        # Create the DraggableGrid for the inventory items
        self.draggableGrid = DraggableGrid(
            self, self.dragManager, self.appconfig, self.currentChapter
        )
        self.draggableGrid.pack(pady=5)

        # Page controls
        self.pageFrame = Frame(self)
        self.pageFrame.pack(side=BOTTOM, fill=X, padx=5, pady=(0, 5))

        self.prevBtn = Label(self.pageFrame, text="⯇ Prev", fg="blue", cursor="hand2")
        self.nextBtn = Label(self.pageFrame, text="Next ⯈", fg="blue", cursor="hand2")
        self.pageLabel = Label(self.pageFrame, text="Page 1")

        # View All button on the same line, positioned after page label
        self.viewAllBtn = Label(
            self.pageFrame, text="⌕ View All", fg="darkgreen", cursor="hand2"
        )

        self.prevBtn.pack(side=LEFT)
        self.pageLabel.pack(side=LEFT, padx=(10, 5))
        self.nextBtn.pack(side=RIGHT)
        self.viewAllBtn.pack(side=RIGHT, padx=(5, 10))

        self.viewAllBtn.bind("<Button-1>", lambda e: self._open_view_all_window())
        self.prevBtn.bind("<Button-1>", lambda e: self._change_page(-1))
        self.nextBtn.bind("<Button-1>", lambda e: self._change_page(1))

    def _load_page(self):
        """Load the current page of storage items into the DraggableGrid."""
        start = self.currentPage * self.ITEMS_PER_PAGE
        end = start + self.ITEMS_PER_PAGE
        page_items = self.storageData[start:end]

        # Load items into the DraggableGrid
        self.draggableGrid.populate_grid(page_items, item_tag="item")

        # Update page label and button states
        self.pageLabel.config(
            text=f"Page {self.currentPage + 1} of {self.page_count()}"
        )
        self.prevBtn.config(state="normal" if self.currentPage > 0 else "disabled")
        self.nextBtn.config(
            state="normal" if self.currentPage < self.page_count() - 1 else "disabled"
        )

        # Re-highlight valid drop zones if we're currently dragging
        if self.dragManager.drag is not None:
            self.dragManager._highlightValidDropZones()

    def _change_page(self, delta):
        new_page = self.currentPage + delta
        if new_page < 0 or new_page >= self.page_count():
            return  # Block going past 0 or above max
        self._save_page()
        self.currentPage = new_page
        self._load_page()

    def _save_page(self):
        # Save current page's items back to storageData
        start = self.currentPage * self.ITEMS_PER_PAGE
        for i, lb in enumerate(self.draggableGrid.listboxes):
            idx = start + i
            if idx < len(self.storageData):
                self.storageData[idx] = lb.getItemId(0) if lb.size() > 0 else 0

    def getListboxes(self):
        """Return the list of DraggableListbox instances in the grid."""
        return self.draggableGrid.listboxes

    def page_count(self):
        return max(
            1, (len(self.storageData) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        )

    def _open_view_all_window(self):
        self._save_page()
        result = open_view_all_window(
            self, self.storageData, self.appconfig, self.currentChapter
        )
        if result is not None:
            self.storageData = result
            self._load_page()

    def getAllItems(self):
        """Get the selected items from all listboxes in the grid."""
        self._save_page()  # Ensure the current page's items are saved before returning
        return (
            self.storageData
        )  # Return the entire storage data, not just selected items
