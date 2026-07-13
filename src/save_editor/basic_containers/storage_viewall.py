from tkinter import Button, Frame, Label, Toplevel
from tkinter.constants import BOTTOM, LEFT, RIGHT, X
from typing import TYPE_CHECKING

from src.save_editor.basic_containers.inventory import Inventory
from src.save_editor.drag.dragmanager import DragManager

if TYPE_CHECKING:
    from src.save_editor.basic_containers.storage import (
        Storage,  # Import Storage for type hinting only
    )


def open_view_all_window(parent: Storage, storageData, appConfig, currentChapter):
    """Open a window showing all storage items for easy management"""

    # Create new window
    view_all_window = Toplevel(parent)
    view_all_window.title("Storage - View All Items")
    view_all_window.transient(parent)  # pyright: ignore[reportArgumentType, reportCallIssue]
    view_all_window.grab_set()

    result = None

    # Create a separate drag manager for this window
    view_all_drag_manager = DragManager(view_all_window, appConfig)

    # Main container frame
    main_frame = Frame(view_all_window)
    main_frame.pack(padx=10, pady=10)

    # Calculate how many pages we need based on the main storage pagination
    total_main_pages = parent.page_count()

    # Create frames and listboxes for each page
    all_listboxes = []

    # Calculate grid layout for page frames (2 columns)
    page_cols = 2

    for page_num in range(total_main_pages):
        # Calculate position in the grid
        frame_row = page_num // page_cols
        frame_col = page_num % page_cols

        # Put a "Inventory" inside this frame
        data = storageData[
            page_num * parent.ITEMS_PER_PAGE : (page_num + 1) * parent.ITEMS_PER_PAGE
        ]
        page_frame = Inventory(
            main_frame,
            f"Page {page_num + 1}",
            appConfig,
            currentChapter,
            data,
            view_all_drag_manager,
        )
        page_frame.grid(
            row=frame_row, column=frame_col, padx=10, pady=10, sticky="nsew"
        )

        all_listboxes.extend(
            page_frame.getListboxes()
        )  # Assuming Inventory has a 'listbox' attribute

    # Configure grid weights for the main frame
    for col in range(page_cols):
        main_frame.columnconfigure(col, weight=1)

    # Register all listboxes with the drag manager for proper highlighting
    for lb in all_listboxes:
        view_all_drag_manager.registerListbox(lb)

    # Populate all listboxes with data
    for i, lb in enumerate(all_listboxes):
        if i < len(storageData):
            item_id = storageData[i]
            lb.insertWithId(0, item_id, "item")  # Use "item" tag for storage items

    # Button frame at bottom
    button_frame = Frame(view_all_window)
    button_frame.pack(side=BOTTOM, fill=X, padx=10, pady=(0, 10))

    def close():
        nonlocal result

        # Save all changes back to storage data
        for i, lb in enumerate(all_listboxes):
            if i < len(storageData):
                if lb.size() > 0:
                    storageData[i] = lb.getItemId(0) or 0
                else:
                    storageData[i] = 0

        result = storageData
        view_all_window.destroy()

    # Add button
    Button(button_frame, text="Close", command=close).pack(side=RIGHT)

    # Add instructions
    Label(
        button_frame,
        text="Drag and drop items to reorganize across all pages.",
        fg="gray",
    ).pack(side=LEFT)

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

    # Wait here until the window is destroyed
    parent.wait_window(view_all_window)

    return result
