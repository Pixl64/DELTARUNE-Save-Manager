from tkinter import Toplevel, Frame, LabelFrame, Label, Button
from tkinter.constants import END, LEFT, RIGHT, TOP, BOTTOM, X, BOTH

from src.save_editor.draggabblelistbox import DragManager, DraggableListbox

class StorageContainer(LabelFrame):
    def __init__(self, parent, title: str, dw_invItems: dict, chapterLimits: dict, currentChapter: int, storageData: list, dragManager: DragManager, itemsPerPage=12, showViewAll=True, appConfig=None):
        super().__init__(parent, text=title)
        self.dw_invItems = dw_invItems  # Item data for context menus
        self.chapterLimits = chapterLimits
        self.currentChapter = currentChapter
        self.dragManager = dragManager
        self.storageData = storageData
        self.itemsPerPage = itemsPerPage
        self.currentPage = 0
        self.lastPageChange = 0  # Track last page change time to prevent rapid changes
        self.showViewAll = showViewAll  # Whether to show the View All button
        self.appConfig = appConfig or chapterLimits

        self.rows = 6
        self.cols = 2

        self.listboxes = []
        self.config(text=title)
        self._build_widgets()
        self._load_page()


    def _build_widgets(self):
        self.gridFrame = Frame(self)
        self.gridFrame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)

        for r in range(self.rows):
            row_listboxes = []
            for c in range(self.cols):
                lb = DraggableListbox(
                    self.gridFrame,
                    self.dragManager,
                    self.appConfig,
                    chapterLimits=self.chapterLimits,
                    chapter=self.currentChapter,
                    allowInternalSwap=True,
                    height=1,
                    width=18,
                )
                lb.grid(row=r, column=c, padx=2, pady=1, sticky="ew")
                row_listboxes.append(lb)
            self.listboxes.extend(row_listboxes)

        # Page controls
        self.pageFrame = Frame(self)
        self.pageFrame.pack(side=BOTTOM, fill=X, padx=5, pady=(0, 5))
        
        self.prevBtn = Label(self.pageFrame, text="⯇ Prev", fg="blue", cursor="hand2")
        self.nextBtn = Label(self.pageFrame, text="Next ⯈", fg="blue", cursor="hand2")
        self.pageLabel = Label(self.pageFrame, text="Page 1")

        self.prevBtn.pack(side=LEFT)
        self.pageLabel.pack(side=LEFT, padx=(10,5))
        self.nextBtn.pack(side=RIGHT)
        self._add_view_all_button()

        self.prevBtn.bind("<Button-1>", lambda e: self._change_page(-1))
        self.nextBtn.bind("<Button-1>", lambda e: self._change_page(1))
        
        # Register page navigation buttons with drag manager for hover functionality
        self.dragManager.registerPageButton(self.prevBtn, lambda: self._change_page_if_possible(-1))
        self.dragManager.registerPageButton(self.nextBtn, lambda: self._change_page_if_possible(1))

    def _add_view_all_button(self):
        """Add View All button next to page label on same line"""
        if self.showViewAll:
            # View All button on the same line, positioned after page label
            self.viewAllBtn = Label(self.pageFrame, text="⌕ View All", fg="darkgreen", cursor="hand2")
            self.viewAllBtn.pack(side=RIGHT, padx=(5, 10))
            self.viewAllBtn.bind("<Button-1>", lambda e: self._open_view_all_window())

    def _load_page(self):
        start = self.currentPage * self.itemsPerPage
        end = start + self.itemsPerPage
        page_items = self.storageData[start:end]
        # Fill or clear all listboxes
        for i, lb in enumerate(self.listboxes):
            lb.delete(0, END)
            lb.itemIds.clear()
            lb.itemTags.clear()
            # Clear any highlighting that might remain
            lb.clearHighlight()
            if i < len(page_items):
                itemId = page_items[i]
                lb.insertWithId(END, itemId, "item")
        self.pageLabel.config(text=f"Page {self.currentPage + 1} / {self.page_count()}")

        # Enable/disable buttons
        self.prevBtn.config(state="normal" if self.currentPage > 0 else "disabled")
        self.nextBtn.config(state="normal" if self.currentPage < self.page_count() - 1 else "disabled")
        
        # Re-highlight valid drop zones if we're currently dragging
        if hasattr(self.dragManager, 'dragStartListbox') and self.dragManager.dragStartListbox is not None:
            self.dragManager._highlightValidDropZones()

    def _change_page(self, delta):
        new_page = self.currentPage + delta
        if new_page < 0 or new_page >= self.page_count():
            return  # Block going past 0 or above max
        self._save_page()
        self.currentPage = new_page
        self._load_page()

    def _change_page_if_possible(self, delta):
        """Change page only if it's possible (used for drag hover functionality)"""
        import time
        current_time = time.time()
        
        # Prevent rapid page changes (cooldown of 0.5 seconds)
        if current_time - self.lastPageChange < 0.5:
            return
            
        new_page = self.currentPage + delta
        if new_page >= 0 and new_page < self.page_count():
            self._save_page()
            self.currentPage = new_page
            self._load_page()
            self.lastPageChange = current_time

    def _save_page(self):
        # Save current page's items back to storageData
        start = self.currentPage * self.itemsPerPage
        for i, lb in enumerate(self.listboxes):
            idx = start + i
            if idx < len(self.storageData):
                self.storageData[idx] = lb.getItemId(0) if lb.size() > 0 else 0

    def page_count(self):
        return max(1, (len(self.storageData) + self.itemsPerPage - 1) // self.itemsPerPage)

    def getListboxes(self):
        return self.listboxes

    def getSelected(self):
        # Return all storage item IDs (flattened)
        self._save_page()
        return self.storageData
    
    def _open_view_all_window(self):
        """Open a window showing all storage items for easy management"""
        # Save current page before opening view all
        self._save_page()
        
        # Create new window
        view_all_window = Toplevel(self)
        view_all_window.title("Storage - View All Items")
        view_all_window.transient(self) # pyright: ignore[reportArgumentType, reportCallIssue]
        view_all_window.grab_set()
        
        # Create a separate drag manager for this window
        view_all_drag_manager = DragManager(view_all_window)
        
        # Main container frame
        main_frame = Frame(view_all_window)
        main_frame.pack(padx=10, pady=10)
        
        # Calculate how many pages we need based on the main storage pagination
        total_main_pages = self.page_count()
        
        # Create frames and listboxes for each page
        all_listboxes = []
        
        # Calculate grid layout for page frames (2 columns)
        page_cols = 2
        
        for page_num in range(total_main_pages):
            # Calculate position in the grid
            frame_row = page_num // page_cols
            frame_col = page_num % page_cols
            
            # Create labeled frame for this page
            page_frame = LabelFrame(main_frame, text=f"Page {page_num + 1}")
            page_frame.grid(row=frame_row, column=frame_col, padx=10, pady=10, sticky="nsew")
            
            # Create 2x6 grid of listboxes within this page frame
            page_listboxes = []
            for r in range(self.rows):  # Use same rows as main storage (6)
                for c in range(self.cols):  # Use same cols as main storage (2)
                    lb = DraggableListbox(
                        page_frame, 
                        view_all_drag_manager, 
                        self.appConfig,
                        chapterLimits=self.chapterLimits, 
                        chapter=self.currentChapter, 
                        allowInternalSwap=True, 
                        height=1, 
                        width=18  # Same width as main storage
                    )
                    lb.grid(row=r, column=c, padx=2, pady=1, sticky="ew")
                    page_listboxes.append(lb)
            
            all_listboxes.extend(page_listboxes)
            
            # Configure grid weights for this page frame
            for col in range(self.cols):
                page_frame.columnconfigure(col, weight=1)
        
        # Configure grid weights for the main frame
        for col in range(page_cols):
            main_frame.columnconfigure(col, weight=1)
        
        # Register all listboxes with the drag manager for proper highlighting
        for lb in all_listboxes:
            view_all_drag_manager.registerListbox(lb)
        
        # Populate all listboxes with data
        for i, lb in enumerate(all_listboxes):
            if i < len(self.storageData):
                item_id = self.storageData[i]
                lb.insertWithId(0, item_id, "item")  # Use "item" tag for storage items
        
        # Button frame at bottom
        button_frame = Frame(view_all_window)
        button_frame.pack(side=BOTTOM, fill=X, padx=10, pady=(0, 10))
        
        def close():
            # Save all changes back to storage data
            for i, lb in enumerate(all_listboxes):
                if i < len(self.storageData):
                    if lb.size() > 0:
                        self.storageData[i] = lb.getItemId(0) or 0
                    else:
                        self.storageData[i] = 0
            
            # Reload the current page in the main storage view
            self._load_page()
            view_all_window.destroy()
        
        # Add button
        Button(button_frame, text="Close", command=close).pack(side=RIGHT)
        
        # Add instructions
        Label(button_frame, text="Drag and drop items to reorganize across all pages.", 
              fg="gray").pack(side=LEFT)
        
        # Focus the window and auto-size to content
        view_all_window.focus_set()
        
        # Let the window size itself to fit the content
        view_all_window.update_idletasks()  # Ensure all widgets are rendered
        view_all_window.resizable(False, False)  # Prevent manual resizing
        
        # Center the window on screen
        window_width = view_all_window.winfo_reqwidth()
        window_height = view_all_window.winfo_reqheight()
        screen_width = view_all_window.winfo_screenwidth()
        screen_height = view_all_window.winfo_screenheight()
        
        # Calculate center position
        center_x = (screen_width - window_width) // 2
        center_y = (screen_height - window_height) // 2
        
        # Set window position
        view_all_window.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
